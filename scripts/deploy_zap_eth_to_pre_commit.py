from brownie import ZapEthToPreCommit, accounts, network
import os

CONTRACTS = {
    "kovan": {
        "weth": "0xd0A1E359811322d97991E03f863a0C30C2cF029C",
        "preCommit": "0xc2BB0EE1f78cC83317727edCC7FDfc1CaF808d0F",
    },
    "mainnet": {
        "weth": "",
        "preCommit": "",
    },
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    contracts = CONTRACTS[net]

    ZapEthToPreCommit.deploy(
        contracts["weth"],
        contracts["preCommit"],
        {"from": account},
        publish_source=True,
    )
