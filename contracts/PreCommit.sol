// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "./interfaces/IVaderBond.sol";
import "./Ownable.sol";

contract PreCommit is Ownable {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    struct Commit {
        uint amount;
        address depositor;
    }

    IVaderBond public immutable bond;
    IERC20 public immutable tokenIn;
    uint public immutable maxCommits;
    uint public immutable minAmountIn;
    uint public immutable maxAmountIn;

    uint public total;
    // true if bond was initialized
    bool public started;
    Commit[] public commits;

    constructor(
        address _bond,
        address _tokenIn,
        uint _maxCommits,
        uint _minAmountIn,
        uint _maxAmountIn
    ) {
        require(_maxAmountIn >= _minAmountIn, "min > max");
        bond = IVaderBond(_bond);
        tokenIn = IERC20(_tokenIn);
        maxCommits = _maxCommits;
        minAmountIn = _minAmountIn;
        maxAmountIn = _maxAmountIn;
    }

    modifier notStarted() {
        require(!started, "started");
        _;
    }

    function reset() external onlyOwner {
        require(started, "not started");
        started = false;
    }

    function count() external view returns (uint) {
        return commits.length;
    }

    function commit(uint _amount) external notStarted {
        require(commits.length < maxCommits, "commits > max");
        require(_amount >= minAmountIn, "amount < min");
        require(_amount <= maxAmountIn, "amount > max");

        tokenIn.safeTransferFrom(msg.sender, address(this), _amount);

        commits.push(Commit({amount: _amount, depositor: msg.sender}));
        total = total.add(_amount);
    }

    function uncommit(uint _index) external notStarted {
        Commit memory commit = commits[_index];
        require(commit.depositor == msg.sender, "not depositor");

        // replace commits[index] with last commit
        uint last = commits.length.sub(1);
        if (last > 0) {
            commits[_index] = commits[last];
        }
        commits.pop();

        total = total.sub(commit.amount);
        // TODO: check memory safe?
        tokenIn.safeTransfer(msg.sender, commit.amount);
    }

    // NOTE: total debt >= Bond.payoutFor(maxAmountIn * maxCommits)
    function init(
        uint _controlVariable,
        uint _vestingTerm,
        uint _minPrice,
        uint _maxPayout,
        uint _maxDebt,
        uint _initialDebt
    ) external onlyOwner notStarted {
        started = true;

        bond.initialize(
            _controlVariable,
            _vestingTerm,
            _minPrice,
            _maxPayout,
            _maxDebt,
            _initialDebt
        );

        tokenIn.approve(address(bond), type(uint).max);

        Commit[] memory _commits = commits;
        uint l = commits.length;
        for (uint i; i < l; i++) {
            // TODO: max bond price?
            bond.deposit(
                _commits[i].amount,
                type(uint).max,
                _commits[i].depositor
            );
        }

        delete commits;
        total = 0;
    }

    function acceptBondOwner() external onlyOwner {
        bond.acceptOwnership();
    }

    function nominateBondOwner() external onlyOwner {
        bond.nominateNewOwner(msg.sender);
    }

    function recover(address _token) external onlyOwner {
        uint bal = IERC20(_token).balanceOf(address(this));

        if (_token == address(tokenIn)) {
            // allow withdraw of excess token in
            IERC20(_token).safeTransfer(msg.sender, bal.sub(total));
        } else {
            IERC20(_token).safeTransfer(msg.sender, bal);
        }
    }
}