// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface IUniswapV2Pair {
    function approve(address spender, uint value) external returns (bool);

    function getReserves()
        external
        view
        returns (
            uint112 _reserve0,
            uint112 _reserve1,
            uint32 _blockTimestampLast
        );
}
