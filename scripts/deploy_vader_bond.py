from brownie import VaderBond, accounts, network

CONTRACTS = {
    "kovan": {
        "treasury": "0xda65ebebEf219f229E69E25a70fE6A8443Ee1aC6",
        "vader": "0xB46dbd07ce34813623FB0643b21DCC8D0268107D",
        "principal": "0xC42706E83433580dd8d865a30e2Ae61082056007",
    },
    "mainnet": {
        "treasury": "",
        "vader": "0x2602278EE1882889B946eb11DC0E810075650983",
        "principal": "",
    },
}


def main():
    account = accounts.load("dev")
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
