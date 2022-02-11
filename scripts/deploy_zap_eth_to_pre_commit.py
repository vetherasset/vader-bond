from brownie import ZapEthToPreCommit, accounts, network
import os

CONTRACTS = {
    "kovan": {
        "weth": "0xd0A1E359811322d97991E03f863a0C30C2cF029C",
        "preCommit": "0x4D9db98d2914C15Ee0295F23cE9CB37626a89b36",
    },
    "mainnet": {
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "preCommit": "0x3db19DE4263284c957B09efe53Cb0e7042228C59",
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
