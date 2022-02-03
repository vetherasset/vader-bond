import brownie
from brownie import TestToken

MAX_COMMITS = 60
MIN_AMOUNT_IN = 10 ** 18
MAX_AMOUNT_IN = 100 * 10 ** 18

MAX_DEBT = 25 * 10 ** 9 * 10 ** 18


def test_constructor(deployer, preCommit, bond, tokenIn):
    assert preCommit.owner() == deployer
    assert preCommit.bond() == bond
    assert preCommit.tokenIn() == tokenIn
    assert preCommit.maxCommits() == MAX_COMMITS
    assert preCommit.minAmountIn() == MIN_AMOUNT_IN
    assert preCommit.maxAmountIn() == MAX_AMOUNT_IN
    assert preCommit.total() == 0
    assert not preCommit.started()


def test_commit(preCommit, tokenIn, user):
    with brownie.reverts("amount < min"):
        preCommit.commit(MIN_AMOUNT_IN - 1, {"from": user})

    with brownie.reverts("amount > max"):
        preCommit.commit(MAX_AMOUNT_IN + 1, {"from": user})

    amount = MAX_AMOUNT_IN
    tokenIn.mint(user, amount)
    tokenIn.approve(preCommit, amount, {"from": user})

    preCommit.commit(amount, {"from": user})

    assert tokenIn.balanceOf(preCommit) == amount
    commit = preCommit.commits(0)
    assert commit["amount"] == amount
    assert commit["depositor"] == user
    assert preCommit.total() == amount
    assert preCommit.count() == 1


def test_uncommit(preCommit, tokenIn, deployer, user):
    with brownie.reverts("not depositor"):
        preCommit.uncommit(0, {"from": deployer})

    commit = preCommit.commits(0)
    preCommit.uncommit(0, {"from": user})

    assert preCommit.total() == 0
    assert preCommit.count() == 0
    assert tokenIn.balanceOf(deployer) == 0
    assert tokenIn.balanceOf(user) == commit["amount"]


def test_accept_bond_owner(preCommit, bond, deployer, user):
    bond.nominateNewOwner(preCommit, {"from": deployer})

    with brownie.reverts("not owner"):
        preCommit.acceptBondOwner({"from": user})

    preCommit.acceptBondOwner({"from": deployer})

    assert bond.owner() == preCommit


def test_init(preCommit, bond, treasury, vader, tokenIn, deployer, user, accounts):
    # bond setup
    treasury.setBondContract(bond, True, {"from": deployer})
    treasury.setMaxPayout(bond, MAX_DEBT, {"from": deployer})
    vader.mint(treasury, MAX_DEBT)

    control_var = 3 * 10 ** 21
    vesting_term = 10000
    min_price = 0.001 * 10 ** 18
    max_payout = 1000
    max_debt = 1e7 * 10 ** 18
    initial_debt = 0

    with brownie.reverts("not owner"):
        preCommit.init(
            control_var,
            vesting_term,
            min_price,
            max_payout,
            max_debt,
            initial_debt,
            {"from": user},
        )

    # check with bond info after init
    data = [{"user": acc.address, "amount": 0} for acc in accounts]

    for i in range(MAX_COMMITS):
        _i = i % len(accounts)
        user = accounts[_i]
        amount = MAX_AMOUNT_IN

        data[_i]["amount"] += amount

        tokenIn.mint(user, amount)
        tokenIn.approve(preCommit, amount, {"from": user})

        preCommit.commit(amount, {"from": user})

    total = preCommit.total()

    tx = preCommit.init(
        control_var,
        vesting_term,
        min_price,
        max_payout,
        max_debt,
        initial_debt,
        {"from": deployer},
    )

    assert preCommit.started()
    assert preCommit.total() == 0
    assert preCommit.count() == 0
    assert tokenIn.balanceOf(preCommit) == 0
    assert tokenIn.balanceOf(bond) == 0
    assert tokenIn.balanceOf(treasury) == total

    for acc, _data in zip(accounts, data):
        bond_info = bond.bondInfo(acc.address)
        payout = bond.payoutFor(_data["amount"])
        assert payout > 0
        assert bond_info["payout"] == payout
        assert bond_info["vesting"] == vesting_term
        assert bond_info["lastBlock"] == tx.block_number

    with brownie.reverts("started"):
        preCommit.init(
            control_var,
            vesting_term,
            min_price,
            max_payout,
            max_debt,
            initial_debt,
            {"from": deployer},
        )

    # test cannot commit after start
    with brownie.reverts("started"):
        preCommit.commit(MIN_AMOUNT_IN, {"from": user})

    # test cannot uncommit after start
    with brownie.reverts("started"):
        preCommit.uncommit(0, {"from": user})


def test_nominate_bond_owner(preCommit, bond, deployer, user):
    with brownie.reverts("not owner"):
        preCommit.nominateBondOwner({"from": user})

    preCommit.nominateBondOwner({"from": deployer})

    assert bond.nominatedOwner() == deployer


def test_reset(preCommit, deployer, user):
    with brownie.reverts("not owner"):
        preCommit.reset({"from": user})

    preCommit.reset({"from": deployer})

    assert not preCommit.started()

    with brownie.reverts("not started"):
        preCommit.reset({"from": deployer})


def test_recover(deployer, user, preCommit, payoutToken):
    token = TestToken.deploy("TEST", "TEST", 18, {"from": deployer})
    token.mint(preCommit, 111)

    with brownie.reverts("not owner"):
        preCommit.recover(
            token,
            {"from": user},
        )

    preCommit.recover(
        token,
        {"from": deployer},
    )

    assert token.balanceOf(preCommit) == 0
