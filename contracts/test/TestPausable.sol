// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../Pausable.sol";

contract TestPausable is Pausable {
    function pause() external {
        _pause();
    }

    function unpause() external {
        _unpause();
    }
}
