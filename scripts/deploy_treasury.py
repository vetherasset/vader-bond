from brownie import Treasury, accounts, network
import os

VADER = {
    "kovan": "0xB46dbd07ce34813623FB0643b21DCC8D0268107D",
    "mainnet": "0x2602278EE1882889B946eb11DC0E810075650983",
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    vader = VADER[net]

    Treasury.deploy(vader, {"from": account}, publish_source=True)
