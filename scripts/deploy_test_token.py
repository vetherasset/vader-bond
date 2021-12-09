from brownie import TestToken, accounts, network


def main():
    account = accounts.load("dev")

    net = network.show_active()
    assert net == "kovan"

    TestToken.deploy("test", "TEST", 18, {"from": account}, publish_source=True)
