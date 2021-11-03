// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "./interfaces/IERC20Metadata.sol";
import "./interfaces/ITreasury.sol";
import "./lib/FixedPoint.sol";
import "./Ownable.sol";

contract VaderBond is Ownable {
    using FixedPoint for FixedPoint.uq112x112;
    using SafeERC20 for IERC20;
    using SafeMath for uint;
    /* ======== EVENTS ======== */
    event BondCreated(uint deposit, uint payout, uint expires);
    event BondRedeemed(address recipient, uint payout, uint remaining);
    event BondPriceChanged(uint internalPrice, uint debtRatio);
    event ControlVariableAdjustment(
        uint initialBCV,
        uint newBCV,
        uint adjustment,
        bool addition
    );

    uint8 public immutable PAYOUT_TOKEN_DECIMALS;

    /* ======== STATE VARIABLES ======== */
    IERC20 public immutable payoutToken; // token paid for principal
    IERC20 public immutable principalToken; // inflow token
    ITreasury public immutable customTreasury; // pays for and receives principal
    address public immutable dao;
    Terms public terms; // stores terms for new bonds
    Adjust public adjustment; // stores adjustment to BCV data
    mapping(address => Bond) public bondInfo; // stores bond information for depositors
    uint public totalDebt; // total value of outstanding bonds; used for pricing
    uint public lastDecay; // reference block for debt decay

    /* ======== STRUCTS ======== */
    // Info for creating new bonds
    struct Terms {
        uint controlVariable; // scaling variable for price
        uint vestingTerm; // in blocks
        uint minimumPrice; // vs principal value
        uint maxPayout; // in thousandths of a %. i.e. 500 = 0.5%
        uint maxDebt; // payout token decimal debt ratio, max % total supply created as debt
    }
    // Info for bond holder
    struct Bond {
        uint payout; // payout token remaining to be paid
        uint vesting; // Blocks left to vest
        uint lastBlock; // Last interaction
    }
    // Info for incremental adjustments to control variable
    struct Adjust {
        bool add; // addition or subtraction
        uint rate; // increment
        uint target; // BCV when adjustment finished
        uint buffer; // minimum length (in blocks) between adjustments
        uint lastBlock; // block when last adjustment made
    }

    /* ======== CONSTRUCTOR ======== */
    constructor(
        address _customTreasury,
        address _payoutToken,
        address _principalToken,
        address _initialOwner,
        address _dao
    ) {
        require(_customTreasury != address(0));
        customTreasury = ITreasury(_customTreasury);
        require(_payoutToken != address(0));
        payoutToken = IERC20(_payoutToken);
        PAYOUT_TOKEN_DECIMALS = IERC20Metadata(_payoutToken).decimals();
        require(_principalToken != address(0));
        principalToken = IERC20(_principalToken);
        require(_initialOwner != address(0));
        owner = _initialOwner;
        require(_dao != address(0));
        dao = _dao;
    }

    /* ======== INITIALIZATION ======== */
    /**
     *  @notice initializes bond parameters
     *  @param _controlVariable uint
     *  @param _vestingTerm uint
     *  @param _minimumPrice uint
     *  @param _maxPayout uint
     *  @param _maxDebt uint
     *  @param _initialDebt uint
     */
    function initializeBond(
        uint _controlVariable,
        uint _vestingTerm,
        uint _minimumPrice,
        uint _maxPayout,
        uint _maxDebt,
        uint _initialDebt
    ) external onlyOwner {
        require(currentDebt() == 0, "Debt must be 0 for initialization");
        terms = Terms({
            controlVariable: _controlVariable,
            vestingTerm: _vestingTerm,
            minimumPrice: _minimumPrice,
            maxPayout: _maxPayout,
            maxDebt: _maxDebt
        });
        totalDebt = _initialDebt;
        lastDecay = block.number;
    }

    /* ======== OWNER FUNCTIONS ======== */
    enum PARAMETER {
        VESTING,
        PAYOUT,
        DEBT
    }

    /**
     *  @notice set parameters for new bonds
     *  @param _parameter PARAMETER
     *  @param _input uint
     */
    function setBondTerms(PARAMETER _parameter, uint _input) external onlyOwner {
        if (_parameter == PARAMETER.VESTING) {
            // 0
            require(_input >= 10000, "Vesting must be longer than 36 hours");
            terms.vestingTerm = _input;
        } else if (_parameter == PARAMETER.PAYOUT) {
            // 1
            require(_input <= 1000, "Payout cannot be above 1 percent");
            terms.maxPayout = _input;
        } else if (_parameter == PARAMETER.DEBT) {
            // 2
            terms.maxDebt = _input;
        }
    }

    /**
     *  @notice set control variable adjustment
     *  @param _addition bool
     *  @param _increment uint
     *  @param _target uint
     *  @param _buffer uint
     */
    function setAdjustment(
        bool _addition,
        uint _increment,
        uint _target,
        uint _buffer
    ) external onlyOwner {
        require(
            _increment <= terms.controlVariable.mul(30).div(1000),
            "Increment too large"
        );
        adjustment = Adjust({
            add: _addition,
            rate: _increment,
            target: _target,
            buffer: _buffer,
            lastBlock: block.number
        });
    }

    /* ======== USER FUNCTIONS ======== */
    /**
     *  @notice deposit bond
     *  @param _amount uint
     *  @param _maxPrice uint
     *  @param _depositor address
     *  @return uint
     */
    function deposit(
        uint _amount,
        uint _maxPrice,
        address _depositor
    ) external returns (uint) {
        require(_depositor != address(0), "Invalid address");

        decayDebt();
        require(totalDebt <= terms.maxDebt, "Max capacity reached");

        uint nativePrice = bondPrice();
        require(_maxPrice >= nativePrice, "Slippage limit: more than max price"); // slippage protection

        uint value = customTreasury.valueOfToken(address(principalToken), _amount);
        uint payout = _payoutFor(value); // payout to bonder is computed

        // TODO: might be a problem with WBTC
        require(payout >= 10**PAYOUT_TOKEN_DECIMALS / 100, "Bond too small"); // must be > 0.01 payout token ( underflow protection )
        require(payout <= maxPayout(), "Bond too large"); // size protection because there is no slippage

        /**
            principal is transferred in
            approved and
            deposited into the treasury, returning (_amount - profit) payout token
         */
        principalToken.safeTransferFrom(msg.sender, address(this), _amount);
        principalToken.approve(address(customTreasury), _amount);
        customTreasury.deposit(address(principalToken), _amount, payout);

        // total debt is increased
        totalDebt = totalDebt.add(value);

        // depositor info is stored
        bondInfo[_depositor] = Bond({
            payout: bondInfo[_depositor].payout.add(payout),
            vesting: terms.vestingTerm,
            lastBlock: block.number
        });

        // indexed events are emitted
        emit BondCreated(_amount, payout, block.number.add(terms.vestingTerm));
        emit BondPriceChanged(_bondPrice(), debtRatio());

        adjust(); // control variable is adjusted
        return payout;
    }

    /**
     *  @notice redeem bond for user
     *  @return uint
     */
    function redeem(address _depositor) external returns (uint) {
        Bond memory info = bondInfo[_depositor];
        uint percentVested = percentVestedFor(_depositor); // (blocks since last interaction / vesting term remaining)

        if (percentVested >= 10000) {
            // if fully vested
            delete bondInfo[_depositor]; // delete user info
            emit BondRedeemed(_depositor, info.payout, 0); // emit bond data
            payoutToken.transfer(_depositor, info.payout);
            return info.payout;
        } else {
            // if unfinished
            // calculate payout vested
            uint payout = info.payout.mul(percentVested).div(10000);

            // store updated deposit info
            bondInfo[_depositor] = Bond({
                payout: info.payout.sub(payout),
                vesting: info.vesting.sub(block.number.sub(info.lastBlock)),
                lastBlock: block.number
            });

            emit BondRedeemed(_depositor, payout, bondInfo[_depositor].payout);
            payoutToken.transfer(_depositor, payout);
            return payout;
        }
    }

    /* ======== INTERNAL HELPER FUNCTIONS ======== */
    /**
     *  @notice makes incremental adjustment to control variable
     */
    function adjust() internal {
        uint blockCanAdjust = adjustment.lastBlock.add(adjustment.buffer);
        if (adjustment.rate != 0 && block.number >= blockCanAdjust) {
            uint initial = terms.controlVariable;
            if (adjustment.add) {
                terms.controlVariable = terms.controlVariable.add(adjustment.rate);
                if (terms.controlVariable >= adjustment.target) {
                    adjustment.rate = 0;
                }
            } else {
                terms.controlVariable = terms.controlVariable.sub(adjustment.rate);
                if (terms.controlVariable <= adjustment.target) {
                    adjustment.rate = 0;
                }
            }
            adjustment.lastBlock = block.number;
            emit ControlVariableAdjustment(
                initial,
                terms.controlVariable,
                adjustment.rate,
                adjustment.add
            );
        }
    }

    /**
     *  @notice reduce total debt
     */
    function decayDebt() internal {
        totalDebt = totalDebt.sub(debtDecay());
        lastDecay = block.number;
    }

    /**
     *  @notice calculate current bond price and remove floor if above
     *  @return price_ uint
     */
    function _bondPrice() internal returns (uint price_) {
        price_ = terms.controlVariable.mul(debtRatio()).div(
            10**(uint(PAYOUT_TOKEN_DECIMALS).sub(5))
        );
        if (price_ < terms.minimumPrice) {
            price_ = terms.minimumPrice;
        } else if (terms.minimumPrice != 0) {
            // TODO: why remove floor?
            terms.minimumPrice = 0;
        }
    }

    /* ======== VIEW FUNCTIONS ======== */
    /**
     *  @notice calculate current bond premium
     *  @return price_ uint
     */
    function bondPrice() public view returns (uint price_) {
        // TODO: why decimals - 5 ?
        // NOTE: debt ratio is scaled up by 10 ** decimals
        price_ = terms.controlVariable.mul(debtRatio()).div(
            10**(uint(PAYOUT_TOKEN_DECIMALS).sub(5))
        );
        if (price_ < terms.minimumPrice) {
            price_ = terms.minimumPrice;
        }
    }

    /**
     *  @notice determine maximum bond size
     *  @return uint
     */
    function maxPayout() public view returns (uint) {
        return payoutToken.totalSupply().mul(terms.maxPayout).div(100000);
    }

    /**
     *  @notice calculate total interest due for new bond
     *  @param _value uint
     *  @return uint
     */
    function _payoutFor(uint _value) internal view returns (uint) {
        // NOTE: scaled up by 1e7
        return FixedPoint.fraction(_value, bondPrice()).decode112with18().div(1e11);
    }

    /**
     *  @notice calculate user's interest due for new bond, accounting for fee
     *  @param _value uint
     *  @return uint
     */
    function payoutFor(uint _value) external view returns (uint) {
        return _payoutFor(_value);
    }

    /**
     *  @notice calculate current ratio of debt to payout token supply
     *  @notice protocols using DAO should be careful when quickly adding large %s to total supply
     *  @return debtRatio_ uint
     */
    function debtRatio() public view returns (uint debtRatio_) {
        // NOTE: debt ratio is scaled up by 10 ** decimals
        debtRatio_ = FixedPoint
            .fraction(
                currentDebt().mul(10**PAYOUT_TOKEN_DECIMALS),
                payoutToken.totalSupply()
            )
            .decode112with18()
            .div(1e18);
    }

    /**
     *  @notice calculate debt factoring in decay
     *  @return uint
     */
    function currentDebt() public view returns (uint) {
        return totalDebt.sub(debtDecay());
    }

    /**
     *  @notice amount to decay total debt by
     *  @return decay_ uint
     */
    function debtDecay() public view returns (uint decay_) {
        uint blocksSinceLast = block.number.sub(lastDecay);
        decay_ = totalDebt.mul(blocksSinceLast).div(terms.vestingTerm);
        if (decay_ > totalDebt) {
            decay_ = totalDebt;
        }
    }

    /**
     *  @notice calculate how far into vesting a depositor is
     *  @param _depositor address
     *  @return percentVested_ uint
     */
    function percentVestedFor(address _depositor)
        public
        view
        returns (uint percentVested_)
    {
        Bond memory bond = bondInfo[_depositor];
        uint blocksSinceLast = block.number.sub(bond.lastBlock);
        uint vesting = bond.vesting;
        if (vesting > 0) {
            percentVested_ = blocksSinceLast.mul(10000).div(vesting);
        } else {
            percentVested_ = 0;
        }
    }

    /**
     *  @notice calculate amount of payout token available for claim by depositor
     *  @param _depositor address
     *  @return pendingPayout_ uint
     */
    function pendingPayoutFor(address _depositor)
        external
        view
        returns (uint pendingPayout_)
    {
        uint percentVested = percentVestedFor(_depositor);
        uint payout = bondInfo[_depositor].payout;
        if (percentVested >= 10000) {
            pendingPayout_ = payout;
        } else {
            pendingPayout_ = payout.mul(percentVested).div(10000);
        }
    }

    /**
     *  @notice allow anyone to send lost tokens (excluding principle or OHM) to the DAO
     */
    function recoverLostToken(address _token) external {
        require(_token != address(payoutToken), "protected token");
        require(_token != address(principalToken), "protected token");
        IERC20(_token).safeTransfer(dao, IERC20(_token).balanceOf(address(this)));
    }
}
