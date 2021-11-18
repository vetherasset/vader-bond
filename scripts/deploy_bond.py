from brownie import VaderBond, accounts

TREASURY = "0x21Fa4114464858DBc182929ED05c5C762d2E4DD3"
PAYOUT = "0x237E9d2F4d4834fD3fCB0ECdeE912682F5D24984"
PRINCIPAL = "0x35d61d5e7fbea90625a4c0fcc1c39d8c4d81818b"


def main():
    account = accounts.load("dev")
    VaderBond.deploy(
        TREASURY, PAYOUT, PRINCIPAL, {"from": account}, publish_source=True
    )
