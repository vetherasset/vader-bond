// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IWETH.sol";
import "./interfaces/IVaderBond.sol";
import "./Ownable.sol";
import "./Pausable.sol";

contract ZapEth is Ownable, Pausable, ReentrancyGuard {
    using SafeMath for uint;

    IWETH public immutable weth;

    IERC20 public immutable vader;
    IVaderBond public immutable bond;

    constructor(
        address _weth,
        address _vader,
        address _bond
    ) {
        require(_weth != address(0), "weth = zero address");
        require(_bond != address(0), "bond = zero address");

        weth = IWETH(_weth);
        vader = IERC20(_vader);
        bond = IVaderBond(_bond);

        // vader bond deposit
        IERC20(_weth).approve(_bond, type(uint).max);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function zap(uint minPayout) external payable nonReentrant whenNotPaused {
        require(msg.value > 0, "value = 0");

        weth.deposit{value: msg.value}();

        // deposit LP for bond
        uint payout = bond.deposit(msg.value, type(uint).max, msg.sender);
        require(payout >= minPayout, "payout < min");
    }

    function recover(address _token) external onlyOwner {
        if (_token != address(0)) {
            IERC20(_token).transfer(
                msg.sender,
                IERC20(_token).balanceOf(address(this))
            );
        } else {
            payable(msg.sender).transfer(address(this).balance);
        }
    }
}
