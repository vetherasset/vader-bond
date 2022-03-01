// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

contract Pausable {
    event Pause(bool _paused);

    bool public paused;

    modifier whenPaused() {
        require(paused, "not paused");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "paused");
        _;
    }

    function _pause() internal whenNotPaused {
        paused = true;
        emit Pause(true);
    }

    function _unpause() internal whenPaused {
        paused = false;
        emit Pause(false);
    }
}
