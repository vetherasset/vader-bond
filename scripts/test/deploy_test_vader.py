from brownie import TestVader, accounts, network


def main():
    account = accounts.load("dev")
    print(f"account: {account}")

    net = network.show_active()
    assert net == "kovan"

    TestVader.deploy({"from": account}, publish_source=True)
