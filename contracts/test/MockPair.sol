// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../interfaces/IUniswapV2Pair.sol";

contract MockPair is IUniswapV2Pair, ERC20 {
    uint112 public reserve0;
    uint112 public reserve1;

    constructor() ERC20("lp", "LP") {}

    function _setReserves_(uint112 _reserve0, uint112 _reserve1) external {
        reserve0 = _reserve0;
        reserve1 = _reserve1;
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
        return (reserve0, reserve1, 0);
    }

    function mint(address _to, uint _amount) external {
        _mint(_to, _amount);
    }
}
