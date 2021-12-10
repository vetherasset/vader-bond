// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../interfaces/IUniswapV2Pair.sol";

contract MockPair is IUniswapV2Pair {
    uint112 public reserve0;

    function _setReserve0_(uint112 _reserve0) external {
        reserve0 = _reserve0;
    }

    function getReserves()
        external
        view
        override
        returns (
            uint112,
            uint112,
            uint32
        )
    {
        return (reserve0, 0, 0);
    }

    function approve(address, uint) external override returns (bool) {
        return true;
    }
}
