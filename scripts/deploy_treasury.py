from brownie import Treasury, accounts

VADER = "0x1fd03e4eA209497910fACE52e5ca39124ef2E8BE"


def main():
    account = accounts.load("dev")
    Treasury.deploy(VADER, {"from": account}, publish_source=True)
