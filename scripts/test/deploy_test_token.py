from brownie import TestToken, accounts, network


def main():
    account = accounts.load("dev")
    print(f"account: {account}")

    net = network.show_active()
    assert net in ["kovan", "rinkeby"]

    TestToken.deploy("test", "TEST", 18, {"from": account}, publish_source=True)
