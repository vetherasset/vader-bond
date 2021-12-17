// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IUniswapV2Router.sol";

contract MockRouter is IUniswapV2Router {
    IERC20 private pair;

    constructor(address _pair) {
        pair = IERC20(_pair);
    }

    uint private _amountToken_;
    uint private _amountEth_;

    function _setAmounts_(uint _amountToken, uint _amountEth) external {
        _amountToken_ = _amountToken;
        _amountEth_ = _amountEth;
    }

    function addLiquidityETH(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    )
        external
        payable
        override
        returns (
            uint amountToken,
            uint amountETH,
            uint liquidity
        )
    {
        require(msg.value > 0, "value = 0");
        IERC20(token).transferFrom(
            msg.sender,
            address(this),
            amountTokenDesired
        );
        liquidity = pair.balanceOf(address(this));
        pair.transfer(msg.sender, liquidity);

        amountToken = _amountToken_;
        amountETH = _amountEth_;

        // refund
        if (amountToken < amountTokenDesired) {
            IERC20(token).transfer(
                msg.sender,
                amountTokenDesired - amountToken
            );
        }
        if (amountETH < msg.value) {
            msg.sender.transfer(msg.value - amountETH);
        }
    }

    function swapExactETHForTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external payable override returns (uint[] memory amounts) {
        address token = path[path.length - 1];

        uint bal = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(msg.sender, bal);

        amounts = new uint[](path.length);
        amounts[path.length - 1] = bal;
    }
}
