from brownie import VaderBond, accounts, network
import os

CONTRACTS = {
    "kovan": {
        "treasury": "0xda65ebebEf219f229E69E25a70fE6A8443Ee1aC6",
        "vader": "0xB46dbd07ce34813623FB0643b21DCC8D0268107D",
        "principal": "0xC42706E83433580dd8d865a30e2Ae61082056007",
    },
    "mainnet": {
        "treasury": "0x8a2afC7a4c2C19E81a79D9158d6bca3858a87B73",
        "vader": "0x2602278EE1882889B946eb11DC0E810075650983",
        "principal": "0x452c60e1E3Ae0965Cd27dB1c7b3A525d197Ca0Aa",
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
