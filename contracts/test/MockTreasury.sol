// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "../interfaces/IERC20Metadata.sol";
import "../interfaces/ITreasury.sol";

contract MockTreasury is ITreasury {
    using SafeMath for uint;

    uint8 private immutable PAYOUT_TOKEN_DECIMALS;
    address public immutable payoutToken;

    constructor(address _payoutToken) {
        payoutToken = _payoutToken;
        PAYOUT_TOKEN_DECIMALS = IERC20Metadata(_payoutToken).decimals();
    }

    function deposit(
        address _principalToken,
        uint _principalAmount,
        uint _payoutAmount
    ) external override {
        IERC20(_principalToken).transferFrom(msg.sender, address(this), _principalAmount);
        IERC20(payoutToken).transfer(msg.sender, _payoutAmount);
    }

    function valueOfToken(address _principalToken, uint _amount) external view override returns (uint value) {
        // convert amount to match payout token decimals
        value = _amount.mul(10**PAYOUT_TOKEN_DECIMALS).div(10**IERC20Metadata(_principalToken).decimals());
    }
}
