from brownie import Treasury, accounts

VADER = "0x237E9d2F4d4834fD3fCB0ECdeE912682F5D24984"


def main():
    account = accounts.load("dev")
    Treasury.deploy(VADER, {"from": account}, publish_source=True)
