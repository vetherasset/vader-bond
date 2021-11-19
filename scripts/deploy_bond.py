from brownie import VaderBond, accounts

TREASURY = "0xD4D721C66bc6acB58321d5673e84c0B1AF245686"
PAYOUT = "0x78CE3ba64Da9D241757603A914b30D992f36Ff24"
PRINCIPAL = "0x35d61d5e7fbea90625a4c0fcc1c39d8c4d81818b"


def main():
    account = accounts.load("dev")
    VaderBond.deploy(
        TREASURY, PAYOUT, PRINCIPAL, {"from": account}, publish_source=True
    )
