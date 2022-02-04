from brownie import Treasury, accounts, network
import os

VADER = {
    "kovan": "0xB46dbd07ce34813623FB0643b21DCC8D0268107D",
    "rinkeby": "0xF79c9406c14AF5Aa8b3F1E5E538A026aDf4D0ff5",
    "mainnet": "0x2602278EE1882889B946eb11DC0E810075650983",
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    vader = VADER[net]

    Treasury.deploy(vader, {"from": account}, publish_source=True)
