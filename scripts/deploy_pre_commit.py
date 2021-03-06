from brownie import PreCommit, accounts, network
import os

ARGS = {
    "rinkeby": {
        "bond": "0x0A23bde5E3930EfEaa546A4b4F10a1b7A9cC1e6C",
        "tokenIn": "0xE8bD273f54a990007b1069a15b66B584abc86e04",
    },
    "kovan": {
        "bond": "0xA8ac19C394783EAcDD36e53686Db037715c87fcD",
        "tokenIn": "0xd0A1E359811322d97991E03f863a0C30C2cF029C",
    },
    "mainnet": {
        "bond": "0xbea19c6AB7F5C90481147Ad69Ff0De2Dba879b5C",
        "tokenIn": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    args = ARGS[net]

    PreCommit.deploy(
        args["bond"],
        args["tokenIn"],
        {"from": account},
        publish_source=True,
    )
