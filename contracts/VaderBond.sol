// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IERC20Metadata.sol";
import "./interfaces/ITreasury.sol";
// import "./lib/FixedPoint.sol";
import "./Ownable.sol";

contract VaderBond is Ownable, ReentrancyGuard {
    // using FixedPoint for FixedPoint.uq112x112;
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    event BondCreated(uint deposit, uint payout, uint expires);
    event BondRedeemed(address indexed recipient, uint payout, uint remaining);
    event BondPriceChanged(uint internalPrice, uint debtRatio);
    event ControlVariableAdjustment(uint initialBCV, uint newBCV, uint adjustment, bool addition);
    event TreasuryChanged(address treasury);

    uint8 private immutable PRINCIPAL_TOKEN_DECIMALS;
    uint8 private constant PAYOUT_TOKEN_DECIMALS = 18; // Vader has 18 decimals
    uint private constant MIN_PAYOUT = 10**PAYOUT_TOKEN_DECIMALS / 100; // 0.01
    uint private constant MAX_PERCENT_VESTED = 1e4; // 1 = 0.01%, 10000 = 100%
    uint private constant MAX_PAYOUT_DENOM = 1e5; // 100 = 0.1%, 100000 = 100%

    IERC20 public immutable payoutToken; // token paid for principal
    IERC20 public immutable principalToken; // inflow token
    ITreasury public treasury; // pays for and receives principal

    Terms public terms; // stores terms for new bonds
    Adjust public adjustment; // stores adjustment to BCV data

    mapping(address => Bond) public bondInfo; // stores bond information for depositors

    uint public totalDebt; // total value of outstanding bonds; used for pricing
    uint public lastDecay; // reference block for debt decay

    // Info for creating new bonds
    struct Terms {
        uint controlVariable; // scaling variable for price
        uint vestingTerm; // in blocks
        uint minPrice; // vs principal value
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

    constructor(
        address _treasury,
        address _payoutToken,
        address _principalToken
    ) {
        require(_treasury != address(0), "treasury = zero address");
        treasury = ITreasury(_treasury);
        require(_payoutToken != address(0), "payout token = zero address");
        payoutToken = IERC20(_payoutToken);
        require(_principalToken != address(0), "");
        principalToken = IERC20(_principalToken);

        PRINCIPAL_TOKEN_DECIMALS = IERC20Metadata(_principalToken).decimals();
    }

    /**
     *  @notice initializes bond parameters
     *  @param _controlVariable uint
     *  @param _vestingTerm uint
     *  @param _minPrice uint
     *  @param _maxPayout uint
     *  @param _maxDebt uint
     *  @param _initialDebt uint
     */
    function initializeBond(
        uint _controlVariable,
        uint _vestingTerm,
        uint _minPrice,
        uint _maxPayout,
        uint _maxDebt,
        uint _initialDebt
    ) external onlyOwner {
        require(currentDebt() == 0, "debt != 0");
        terms = Terms({
            controlVariable: _controlVariable,
            vestingTerm: _vestingTerm,
            minPrice: _minPrice,
            maxPayout: _maxPayout,
            maxDebt: _maxDebt
        });
        totalDebt = _initialDebt;
        lastDecay = block.number;
    }

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
            require(_input <= MAX_PAYOUT_DENOM / 100, "Payout cannot be above 1 percent");
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
        require(_increment <= terms.controlVariable.mul(30) / 1000, "Increment too large");
        adjustment = Adjust({
            add: _addition,
            rate: _increment,
            target: _target,
            buffer: _buffer,
            lastBlock: block.number
        });
    }

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
    ) external nonReentrant returns (uint) {
        require(_depositor != address(0), "Invalid address");

        decayDebt();
        require(totalDebt <= terms.maxDebt, "Max capacity reached");
        require(_maxPrice >= bondPrice(), "Slippage limit: more than max price");

        uint value = treasury.valueOfToken(address(principalToken), _amount);
        uint payout = payoutFor(value); // payout to bonder is computed

        require(payout >= MIN_PAYOUT, "Bond too small");
        // size protection because there is no slippage
        require(payout <= maxPayout(), "Bond too large");

        principalToken.safeTransferFrom(msg.sender, address(this), _amount);
        principalToken.approve(address(treasury), _amount);
        treasury.deposit(address(principalToken), _amount, payout);

        totalDebt = totalDebt.add(value);

        bondInfo[_depositor] = Bond({
            payout: bondInfo[_depositor].payout.add(payout),
            vesting: terms.vestingTerm,
            lastBlock: block.number
        });

        emit BondCreated(_amount, payout, block.number.add(terms.vestingTerm));

        uint price = bondPrice();
        // remove floor if price above min
        if (price > terms.minPrice && terms.minPrice > 0) {
            terms.minPrice = 0;
        }

        emit BondPriceChanged(price, debtRatio());

        adjust(); // control variable is adjusted
        return payout;
    }

    /**
     *  @notice redeem bond for user
     *  @return uint
     */
    function redeem(address _depositor) external nonReentrant returns (uint) {
        Bond memory info = bondInfo[_depositor];
        uint percentVested = percentVestedFor(_depositor); // (blocks since last interaction / vesting term remaining)

        if (percentVested >= MAX_PERCENT_VESTED) {
            // if fully vested
            delete bondInfo[_depositor]; // delete user info
            emit BondRedeemed(_depositor, info.payout, 0); // emit bond data
            payoutToken.transfer(_depositor, info.payout);
            return info.payout;
        } else {
            // if unfinished
            // calculate payout vested
            uint payout = info.payout.mul(percentVested) / MAX_PERCENT_VESTED;

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

    /**
     *  @notice makes incremental adjustment to control variable
     */
    function adjust() private {
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
            emit ControlVariableAdjustment(initial, terms.controlVariable, adjustment.rate, adjustment.add);
        }
    }

    /**
     *  @notice amount to decay total debt by
     *  @return decay uint
     */
    function debtDecay() public view returns (uint decay) {
        uint blocksSinceLast = block.number.sub(lastDecay);
        decay = totalDebt.mul(blocksSinceLast).div(terms.vestingTerm);
        if (decay > totalDebt) {
            decay = totalDebt;
        }
    }

    /**
     *  @notice reduce total debt
     */
    function decayDebt() private {
        totalDebt = totalDebt.sub(debtDecay());
        lastDecay = block.number;
    }

    /**
     *  @notice calculate debt factoring in decay
     *  @return uint
     */
    function currentDebt() public view returns (uint) {
        return totalDebt.sub(debtDecay());
    }

    /**
     *  @notice calculate current ratio of debt to payout token supply
     *  @notice protocols using DAO should be careful when quickly adding large %s to total supply
     *  @return uint
     */
    function debtRatio() public view returns (uint) {
        // TODO: use fraction?
        // return
        //     FixedPoint
        //         .fraction(currentDebt().mul(10**PAYOUT_TOKEN_DECIMALS), payoutToken.totalSupply())
        //         .decode112with18() / 1e18;
        // NOTE: debt ratio is scaled up by 1e18
        return currentDebt().mul(1e18).div(payoutToken.totalSupply());
    }

    /**
     *  @notice calculate current bond premium
     *  @return price uint
     */
    function bondPrice() public view returns (uint price) {
        // NOTE: bond price scaled to principal token decimals
        // NOTE: debt ratio scaled up with 1e18, so we divide here
        price = terms.controlVariable.mul(debtRatio()).mul(10**PRINCIPAL_TOKEN_DECIMALS) / 1e18;
        if (price < terms.minPrice) {
            price = terms.minPrice;
        }
    }

    /**
     *  @notice determine maximum bond size
     *  @return uint
     */
    function maxPayout() public view returns (uint) {
        return payoutToken.totalSupply().mul(terms.maxPayout) / MAX_PAYOUT_DENOM;
    }

    /**
     *  @notice calculate total interest due for new bond
     *  @param _value uint
     *  @return uint
     */
    function payoutFor(uint _value) public view returns (uint) {
        // TODO: use fraction?
        // NOTE: scaled up by 1e7
        // return FixedPoint.fraction(_value, bondPrice()).decode112with18() / 1e11;

        /*
        B = amount of bond to payout
        A = amount of principal token in
        P = amount of principal token to pay to get 1 bond

        B = A / P
        */
        // NOTE: value must match payout token decimals
        // NOTE: bond price matches principal token decimals
        return _value.mul(10**PRINCIPAL_TOKEN_DECIMALS).div(bondPrice());
    }

    /**
     *  @notice calculate how far into vesting a depositor is
     *  @param _depositor address
     *  @return percentVested uint
     */
    function percentVestedFor(address _depositor) public view returns (uint percentVested) {
        Bond memory bond = bondInfo[_depositor];
        uint blocksSinceLast = block.number.sub(bond.lastBlock);
        uint vesting = bond.vesting;
        if (vesting > 0) {
            percentVested = blocksSinceLast.mul(MAX_PERCENT_VESTED).div(vesting);
        }
        // default percentVested = 0
    }

    /**
     *  @notice calculate amount of payout token available for claim by depositor
     *  @param _depositor address
     *  @return pendingPayout uint
     */
    function pendingPayoutFor(address _depositor) external view returns (uint pendingPayout) {
        uint percentVested = percentVestedFor(_depositor);
        uint payout = bondInfo[_depositor].payout;
        if (percentVested >= MAX_PERCENT_VESTED) {
            pendingPayout = payout;
        } else {
            pendingPayout = payout.mul(percentVested) / MAX_PERCENT_VESTED;
        }
    }

    /**
     *  @notice owner can update treasury address
     *  @param _treasury address
     *  @dev allow new treasury to be zero address
     */
    function setTreasury(address _treasury) external onlyOwner {
        require(_treasury != address(treasury), "no change");
        treasury = ITreasury(_treasury);
        emit TreasuryChanged(_treasury);
    }

    /**
     *  @notice allows owner to send lost tokens to owner
     *  @param _token address
     */
    function recoverLostToken(address _token) external onlyOwner {
        IERC20(_token).safeTransfer(owner, IERC20(_token).balanceOf(address(this)));
    }
}
