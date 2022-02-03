// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./interfaces/IOwnable.sol";

contract Ownable is IOwnable {
    event OwnerNominated(address newOwner);
    event OwnerChanged(address newOwner);

    address public owner;
    address public nominatedOwner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function nominateNewOwner(address _owner) external override onlyOwner {
        nominatedOwner = _owner;
        emit OwnerNominated(_owner);
    }

    function acceptOwnership() external override {
        require(msg.sender == nominatedOwner, "not nominated");

        owner = msg.sender;
        nominatedOwner = address(0);

        emit OwnerChanged(msg.sender);
    }
}
