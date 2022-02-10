import brownie
from brownie import ZERO_ADDRESS


def test_constructor(deployer, zapEthToPreCommit, weth, preCommitWeth):
    zap = zapEthToPreCommit
    preCommit = preCommitWeth

    assert zap.owner() == deployer
    assert zap.weth() == weth
    assert zap.preCommit() == preCommit

    assert weth.allowance(zap, preCommit) == 2 ** 256 - 1


def test_zap(zapEthToPreCommit, preCommitWeth, user):
    zap = zapEthToPreCommit
    preCommit = preCommitWeth

    zap.zap({"from": user, "value": 1e18})

    commit = preCommit.commits(0)
    assert commit["depositor"] == user
    assert commit["amount"] == 1e18


def test_recover(deployer, zapEthToPreCommit, weth, user):
    zap = zapEthToPreCommit

    with brownie.reverts("not owner"):
        zap.recover(ZERO_ADDRESS, {"from": user})

    # test recover token
    zap.recover(weth, {"from": deployer})

    # test recover ETH
    zap.recover(ZERO_ADDRESS, {"from": deployer})
