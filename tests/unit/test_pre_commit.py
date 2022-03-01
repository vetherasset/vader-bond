import brownie
from brownie import ZERO_ADDRESS, TestToken

MAX_COMMITS = 50
MIN_AMOUNT_IN = int(0.01 * 10 ** 18)
MAX_AMOUNT_IN = int(10 * 10 ** 18)

MAX_DEBT = int(25 * 10 ** 9 * 10 ** 18)


def test_constructor(deployer, preCommit, bond, tokenIn):
    assert preCommit.owner() == deployer
    assert preCommit.bond() == bond
    assert preCommit.tokenIn() == tokenIn
    assert preCommit.maxCommits() == 0
    assert preCommit.minAmountIn() == 0
    assert preCommit.maxAmountIn() == 0
    assert preCommit.total() == 0
    assert not preCommit.open()


def test_start(preCommit, deployer, user):
    with brownie.reverts("not owner"):
        preCommit.start(MAX_COMMITS, MIN_AMOUNT_IN, MAX_AMOUNT_IN, {"from": user})

    preCommit.start(MAX_COMMITS, MIN_AMOUNT_IN, MAX_AMOUNT_IN, {"from": deployer})

    assert preCommit.open()
    assert preCommit.maxCommits() == MAX_COMMITS
    assert preCommit.minAmountIn() == MIN_AMOUNT_IN
    assert preCommit.maxAmountIn() == MAX_AMOUNT_IN

    with brownie.reverts("not closed"):
        preCommit.start(MAX_COMMITS, MIN_AMOUNT_IN, MAX_AMOUNT_IN, {"from": deployer})


def test_commit(preCommit, tokenIn, deployer, user):
    with brownie.reverts("depositor = zero address"):
        preCommit.commit(ZERO_ADDRESS, MIN_AMOUNT_IN, {"from": user})

    with brownie.reverts("amount < min"):
        preCommit.commit(user, MIN_AMOUNT_IN - 1, {"from": user})

    with brownie.reverts("amount > max"):
        preCommit.commit(user, MAX_AMOUNT_IN + 1, {"from": user})

    amount = MAX_AMOUNT_IN
    tokenIn.mint(user, amount)
    tokenIn.approve(preCommit, amount, {"from": user})

    preCommit.commit(user, amount, {"from": user})

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

    control_var = 5 * 10 ** 10
    vesting_term = 10000
    min_price = 1e11
    max_payout = 1000
    max_debt = 5 * 10 ** 25
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
        # amount = MAX_AMOUNT_IN
        amount = MIN_AMOUNT_IN

        data[_i]["amount"] += amount

        tokenIn.mint(user, amount)
        tokenIn.approve(preCommit, amount, {"from": user})

        preCommit.commit(user, amount, {"from": user})

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

    assert not preCommit.open()
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

    with brownie.reverts("not open"):
        preCommit.init(
            control_var,
            vesting_term,
            min_price,
            max_payout,
            max_debt,
            initial_debt,
            {"from": deployer},
        )

    # test cannot commit after init
    with brownie.reverts("not open"):
        preCommit.commit(user, MIN_AMOUNT_IN, {"from": user})

    # test cannot uncommit after init
    with brownie.reverts("not open"):
        preCommit.uncommit(0, {"from": user})


def test_nominate_bond_owner(preCommit, bond, deployer, user):
    with brownie.reverts("not owner"):
        preCommit.nominateBondOwner({"from": user})

    preCommit.nominateBondOwner({"from": deployer})

    assert bond.nominatedOwner() == deployer


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
