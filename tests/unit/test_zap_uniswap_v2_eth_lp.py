import brownie
from brownie import ZERO_ADDRESS, VaderBond, ZapUniswapV2EthLp


WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"


def test_constructor(deployer, zapUniswapV2EthLp, router, pair, vader, bond):
    zap = zapUniswapV2EthLp

    assert zap.WETH() == WETH
    assert zap.router() == router
    assert zap.pair() == pair
    assert zap.vader() == vader
    assert zap.bond() == bond
    assert zap.owner() == deployer

    assert vader.allowance(zap, router) == 2 ** 256 - 1
    assert pair.allowance(zap, bond) == 2 ** 256 - 1


def test_pause(deployer, user, zapUniswapV2EthLp):
    zap = zapUniswapV2EthLp

    with brownie.reverts("not owner"):
        zap.pause({"from": user})

    tx = zap.pause({"from": deployer})

    assert tx.events["Pause"].values() == [True]
    assert zap.paused()

    with brownie.reverts("paused"):
        zap.pause({"from": deployer})


def test_unpause(deployer, user, zapUniswapV2EthLp):
    zap = zapUniswapV2EthLp

    with brownie.reverts("not owner"):
        zap.unpause({"from": user})

    tx = zap.unpause({"from": deployer})

    assert tx.events["Pause"].values() == [False]
    assert not zap.paused()

    with brownie.reverts("not paused"):
        zap.unpause({"from": deployer})


CONTROL_VAR = int(3 * 1e21)
VESTING_TERM = 10000
MIN_PRICE = int(0.001 * 1e18)
MAX_PAYOUT = 1000
MAX_DEBT = int(1e7 * 1e18)
INITIAL_DEBT = 0


def test_zap(deployer, router, pair, vader, treasury, user):

    # setup
    bond = VaderBond.deploy(treasury, vader, pair, {"from": deployer})

    bond.initialize(
        CONTROL_VAR,
        VESTING_TERM,
        MIN_PRICE,
        MAX_PAYOUT,
        MAX_DEBT,
        INITIAL_DEBT,
        {"from": deployer},
    )

    treasury.setBondContract(bond, True, {"from": deployer})
    treasury.setMaxPayout(bond, MAX_DEBT, {"from": deployer})

    zap = ZapUniswapV2EthLp.deploy(WETH, router, pair, vader, bond, {"from": deployer})

    vader.mint(treasury, MAX_DEBT)
    eth_in = 1e18
    vader_out = 30 * 1e18
    reserve_0 = 300 * 1e18
    reserve_1 = 10 * 1e18

    pair._setReserves_(reserve_0, reserve_1)

    eth_swap = zap.calculateSwapInAmount(reserve_0, eth_in)
    vader.mint(router, vader_out)

    lp_amount = 50 * 1e18
    pair.mint(router, lp_amount)

    router._setAmounts_(0.9 * vader_out, 0.8 * (eth_in - eth_swap))

    # test paused
    zap.pause({"from": deployer})

    with brownie.reverts("paused"):
        zap.zap(0, {"from": user, "value": 0})

    zap.unpause({"from": deployer})

    with brownie.reverts("value = 0"):
        zap.zap(0, {"from": user, "value": 0})

    with brownie.reverts("payout < min"):
        zap.zap(2 ** 256 - 1, {"from": user, "value": eth_in})

    value = treasury.valueOfToken(pair, lp_amount)
    min_payout = bond.payoutFor(value)
    assert min_payout > 0
    tx = zap.zap(min_payout, {"from": user, "value": eth_in})

    bond_info = bond.bondInfo(user)
    assert bond_info["payout"] > 0
    assert bond_info["vesting"] > 0
    assert bond_info["lastBlock"] == tx.block_number


def test_recover(deployer, zapUniswapV2EthLp, vader, user):
    zap = zapUniswapV2EthLp

    with brownie.reverts("not owner"):
        zap.recover(ZERO_ADDRESS, {"from": user})

    # test recover token
    zap.recover(vader, {"from": deployer})

    # test recover ETH
    zap.recover(ZERO_ADDRESS, {"from": deployer})
