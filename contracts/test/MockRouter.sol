// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../interfaces/IUniswapV2Router.sol";

contract MockRouter is IUniswapV2Router {
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
    {}

    function swapExactETHForTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external payable override returns (uint[] memory amounts) {}
}
