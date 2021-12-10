// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IUniswapV2Router.sol";
import "./interfaces/IUniswapV2Pair.sol";
import "./interfaces/IVaderBond.sol";
import "./Ownable.sol";

contract ZapEth is Ownable, ReentrancyGuard {
    using SafeMath for uint;

    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    // 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
    IUniswapV2Router public immutable router;
    // 0x452c60e1E3Ae0965Cd27dB1c7b3A525d197Ca0Aa
    IUniswapV2Pair public immutable pair;

    // 0x2602278EE1882889B946eb11DC0E810075650983
    IERC20 public immutable vader;
    IVaderBond public immutable bond;

    constructor(
        address _router,
        address _pair,
        address _vader,
        address _bond
    ) {
        require(_router != address(0), "router = zero address");
        require(_bond != address(0), "bond = zero address");

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

    function _swap(uint amount) private returns (uint) {
        address[] memory path = new address[](2);
        path[0] = WETH;
        path[1] = address(vader);

        uint[] memory amounts = router.swapExactETHForTokens{value: amount}(
            0,
            path,
            address(this),
            block.timestamp
        );

        return amounts[1];
    }

    function zap(uint minPayout) external payable nonReentrant {
        require(msg.value > 0, "value = 0");

        // reserve 0 = Vader
        (uint reserve0, , ) = pair.getReserves();
        uint ethIn = _calculateSwapInAmount(reserve0, msg.value);

        // swap ETH to Vader
        uint vaderOut = _swap(ethIn);

        // add liquidity
        uint bal = msg.value - ethIn;
        (uint amountVader, uint amountEth, uint lp) = router.addLiquidityETH{
            value: bal
        }(address(vader), vaderOut, 1, 1, address(this), block.timestamp);

        // refund Vader
        if (amountVader < vaderOut) {
            vader.transfer(msg.sender, vaderOut - amountVader);
        }
        // refund ETH
        if (amountEth < bal) {
            (bool ok, ) = msg.sender.call{value: bal - amountEth}("");
            require(ok, "refund ETH failed");
        }

        // deposit LP for bond
        uint payout = bond.deposit(lp, type(uint).max, msg.sender);
        require(payout >= minPayout);
    }

    function recover(address _token) external onlyOwner {
        if (_token != address(0)) {
            IERC20(_token).transfer(
                owner,
                IERC20(_token).balanceOf(address(this))
            );
        } else {
            payable(owner).transfer(address(this).balance);
        }
    }
}
