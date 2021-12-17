// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract TestVader is ERC20 {
    constructor() ERC20("Test Vader", "TEST VADER") {
        _mint(address(this), 25 * 1e9 * 1e18);
    }

    function mint(address _to, uint _amount) external {
        _transfer(address(this), _to, _amount);
    }
}
