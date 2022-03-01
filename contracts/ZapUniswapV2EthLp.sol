// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IUniswapV2Router.sol";
import "./interfaces/IUniswapV2Pair.sol";
import "./interfaces/IVaderBond.sol";
import "./Ownable.sol";
import "./Pausable.sol";

contract ZapUniswapV2EthLp is Ownable, Pausable, ReentrancyGuard {
    using SafeMath for uint;

    address public immutable WETH;

    IUniswapV2Router public immutable router;
    IUniswapV2Pair public immutable pair;

    IERC20 public immutable vader;
    IVaderBond public immutable bond;

    constructor(
        address _weth,
        address _router,
        address _pair,
        address _vader,
        address _bond
    ) {
        require(_weth != address(0), "weth = zero address");
        require(_router != address(0), "router = zero address");
        require(_bond != address(0), "bond = zero address");

        WETH = _weth;
        router = IUniswapV2Router(_router);
        pair = IUniswapV2Pair(_pair);

        vader = IERC20(_vader);
        bond = IVaderBond(_bond);

        // uniswap add liquidity
        IERC20(_vader).approve(_router, type(uint).max);
        // vader bond deposit
        IERC20(_pair).approve(_bond, type(uint).max);
    }

    // Uniswap may refund
    receive() external payable {}

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function _sqrt(uint y) private pure returns (uint z) {
        if (y > 3) {
            z = y;
            uint x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    function _calculateSwapInAmount(uint reserveIn, uint userIn)
        private
        pure
        returns (uint)
    {
        return
            _sqrt(reserveIn.mul(userIn.mul(3988000) + reserveIn.mul(3988009)))
                .sub(reserveIn.mul(1997)) / 1994;
    }

    function calculateSwapInAmount(uint reserveIn, uint userIn)
        external
        pure
        returns (uint)
    {
        return _calculateSwapInAmount(reserveIn, userIn);
    }

    function _swap(uint amount) private returns (uint) {
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = address(vader);

        return
            router.swapExactETHForTokens{value: amount}(
                1,
                path,
                address(this),
                block.timestamp
            )[1];
    }

    function zap(uint minPayout) external payable nonReentrant whenNotPaused {
        require(msg.value > 0, "value = 0");

        // reserve 0 = Vader
        (uint reserve0, , ) = pair.getReserves();
        uint ethSwapAmount = _calculateSwapInAmount(reserve0, msg.value);

        // swap ETH to Vader
        uint vaderOut = _swap(ethSwapAmount);

        // add liquidity
        uint ethIn = msg.value.sub(ethSwapAmount);
        (uint amountVader, uint amountEth, uint lp) = router.addLiquidityETH{
            value: ethIn
        }(address(vader), vaderOut, 1, 1, address(this), block.timestamp);

        // refund Vader
        if (amountVader < vaderOut) {
            vader.transfer(msg.sender, vaderOut - amountVader);
        }
        // refund ETH
        if (amountEth < ethIn) {
            (bool ok, ) = msg.sender.call{value: ethIn - amountEth}("");
            require(ok, "refund ETH failed");
        }

        // deposit LP for bond
        uint payout = bond.deposit(lp, type(uint).max, msg.sender);
        require(payout >= minPayout, "payout < min");
    }

    function recover(address _token) external onlyOwner {
        if (_token != address(0)) {
            IERC20(_token).transfer(
                msg.sender,
                IERC20(_token).balanceOf(address(this))
            );
        } else {
            payable(msg.sender).transfer(address(this).balance);
        }
    }
}
