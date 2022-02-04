from brownie import PreCommit, accounts, network
import os

ARGS = {
    "rinkeby": {
        "bond": "0x0A23bde5E3930EfEaa546A4b4F10a1b7A9cC1e6C",
        "token_in": "0xE8bD273f54a990007b1069a15b66B584abc86e04",
        "max_commits": 100,
        "min_amount_in": 0.01 * 10 ** 18,
        "max_amount_in": 10 * 10 ** 18,
    },
    "mainnet": {
        # TODO: params
        "bond": "",
        "token_in": "",
        "max_commits": 100,
        "min_amount_in": 0,
        "max_amount_in": 0,
    },
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    args = ARGS[net]

    PreCommit.deploy(
        args["bond"],
        args["token_in"],
        args["max_commits"],
        args["min_amount_in"],
        args["max_amount_in"],
        {"from": account},
        publish_source=True,
    )
