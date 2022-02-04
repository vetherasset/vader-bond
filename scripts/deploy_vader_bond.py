from brownie import VaderBond, accounts, network
import os

CONTRACTS = {
    "kovan": {
        "treasury": "0x666266f24E17d9ab7bCb25715C75146143E16c39",
        "vader": "0xB46dbd07ce34813623FB0643b21DCC8D0268107D",
        # Uniswap ETH - Vader LP
        # "principal": "0xC42706E83433580dd8d865a30e2Ae61082056007",
        # WETH
        "principal": "0xd0A1E359811322d97991E03f863a0C30C2cF029C",
    },
    "rinkeby": {
        "treasury": "0xEa66FB7590147A5C901E14034f243e1cF8f958ff",
        "vader": "0xF79c9406c14AF5Aa8b3F1E5E538A026aDf4D0ff5",
        "principal": "0xE8bD273f54a990007b1069a15b66B584abc86e04",
    },
    "mainnet": {
        "treasury": "0x8a2afC7a4c2C19E81a79D9158d6bca3858a87B73",
        "vader": "0x2602278EE1882889B946eb11DC0E810075650983",
        # Uniswap ETH - Vader LP
        # "principal": "0x452c60e1E3Ae0965Cd27dB1c7b3A525d197Ca0Aa",
        # WETH
        "principal": "",
    },
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    contracts = CONTRACTS[net]

    VaderBond.deploy(
        contracts["treasury"],
        contracts["vader"],
        contracts["principal"],
        {"from": account},
        publish_source=True,
    )
