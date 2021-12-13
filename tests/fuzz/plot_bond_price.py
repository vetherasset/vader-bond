import brownie
from brownie import ZERO_ADDRESS

import matplotlib.pyplot as plt
import numpy as np

## Terms
CONTROL_VAR = int(3 * 1e21)
VESTING_TERM = 10000
MIN_PRICE = int(0.001 * 1e18)
MAX_PAYOUT = 1000
MAX_DEBT = int(1e7 * 1e18)
INITIAL_DEBT = 0
PAYOUT_TOTAL_SUPPLY = int(25 * 1e9 * 1e18)

## Adjustment
ADD = True
RATE = int(0.03 * CONTROL_VAR)
TARGET = CONTROL_VAR * 2
BUFFER = 1


def test(chain, deployer, user, bond, treasury, principalToken, payoutToken):
    treasury.setBondContract(bond, True, {"from": deployer})

    bond.initialize(
        CONTROL_VAR,
        VESTING_TERM,
        MIN_PRICE,
        MAX_PAYOUT,
        MAX_DEBT,
        INITIAL_DEBT,
        {"from": deployer},
    )

    bond.setAdjustment(
        ADD,
        RATE,
        TARGET,
        BUFFER,
        {"from": deployer},
    )

    payoutToken.mint(treasury, PAYOUT_TOTAL_SUPPLY)

    principalToken.mint(user, 2 ** 256 - 1)
    principalToken.approve(bond, 2 ** 256 - 1, {"from": user})

    max_price = 2 ** 256 - 1

    block = 0

    blocks = []
    debt_ratios = []
    cvs = []
    prices = []

    def snapshot():
        debt_ratio = bond.debtRatio()
        price = bond.bondPrice()
        cv = bond.terms()["controlVariable"]
        # normalized
        print("block", block, debt_ratio / 1e18, price / 1e18, cv / 1e18)

        blocks.append(block)
        debt_ratios.append(debt_ratio / 1e18)
        prices.append(price / 1e18)
        cvs.append(cv / 1e18)

    for j in range(10):
        print("--- deposit ---")
        for i in range(10):
            snapshot()
            bond.deposit(1000 * 1e18, max_price, user, {"from": user})
            block += 1

        print("--- wait ---")
        for i in range(10):
            wait = 10
            chain.mine(wait)
            block += wait
            snapshot()

    plt.plot(blocks, prices, label="price")
    plt.plot(blocks, debt_ratios, label="debt ratio")
    plt.plot(blocks, cvs, label="control var")
    plt.legend()
    plt.savefig("bond-price.png")
