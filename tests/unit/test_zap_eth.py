import brownie
from brownie import ZERO_ADDRESS


def test_constructor(deployer, zapEth, router, pair, payoutToken, bond):
    vader = payoutToken

    assert zapEth.router() == router
    assert zapEth.pair() == pair
    assert zapEth.vader() == vader
    assert zapEth.bond() == bond
    assert zapEth.owner() == deployer
