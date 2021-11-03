// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

contract Ownable {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(owner == msg.sender, "Ownable: caller is not the owner");
        _;
    }

    function transferManagment(address _newOwner) external onlyOwner {
        require(_newOwner != address(0));
        owner = _newOwner;
    }
}
