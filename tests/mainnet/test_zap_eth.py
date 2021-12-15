import brownie
from brownie import ZapEth, VaderBond, Treasury
import pytest

## Terms
CONTROL_VAR = int(3 * 1e21)
VESTING_TERM = 10000
MIN_PRICE = int(0.001 * 1e18)
MAX_PAYOUT = 1000
MAX_DEBT = int(1e7 * 1e18)
INITIAL_DEBT = 0
PAYOUT_TOTAL_SUPPLY = int(25 * 1e9 * 1e18)


WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
# Uniswap V2 router
ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"


def test_zap_eth(deployer, lp, vader, vader_whale, user):
    treasury = Treasury.deploy(vader, {"from": deployer})
    bond = VaderBond.deploy(treasury, vader, lp, {"from": deployer})

    treasury.setBondContract(bond, True, {"from": deployer})
    treasury.setMaxPayout(bond, 1e6 * 1e18, {"from": deployer})
    vader.transfer(treasury, 1e6 * 1e18, {"from": vader_whale})

    bond.initialize(
        CONTROL_VAR,
        VESTING_TERM,
        MIN_PRICE,
        MAX_PAYOUT,
        MAX_DEBT,
        INITIAL_DEBT,
        {"from": deployer},
    )

    zap = ZapEth.deploy(WETH, ROUTER, lp, vader, bond, {"from": deployer})

    # eth_in = zap.calculateSwapInAmount(88705347675249280153804878, 1e18)
    # print(eth_in, eth_in <= 1e18)

    tx = zap.zap(1, {"from": user, "value": 1e18})

    bond_info = bond.bondInfo(user)
    assert bond_info["payout"] > 0
    assert bond_info["vesting"] > 0
    assert bond_info["lastBlock"] == tx.block_number
