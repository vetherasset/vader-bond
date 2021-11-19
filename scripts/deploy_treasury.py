from brownie import Treasury, accounts

VADER = "0x78CE3ba64Da9D241757603A914b30D992f36Ff24"


def main():
    account = accounts.load("dev")
    Treasury.deploy(VADER, {"from": account}, publish_source=True)
