from brownie import ZapEth, accounts, network
import os

CONTRACTS = {
    "kovan": {
        "weth": "0xd0A1E359811322d97991E03f863a0C30C2cF029C",
        "bond": "0xA8ac19C394783EAcDD36e53686Db037715c87fcD",
    },
    "mainnet": {
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "bond": "",
    },
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    contracts = CONTRACTS[net]

    ZapEth.deploy(
        contracts["weth"],
        contracts["bond"],
        {"from": account},
        publish_source=True,
    )
