from brownie import VaderBond, accounts

TREASURY = "0x15d89713eA5C46dE381C51A34fE4C743677576B4"
PAYOUT = "0x1fd03e4eA209497910fACE52e5ca39124ef2E8BE"
PRINCIPAL = "0x38F19a5452B03262203cAe9532Fbfd211fa32FF1"


def main():
    account = accounts.load("dev")
    print(f"account: {account}")

    VaderBond.deploy(
        TREASURY, PAYOUT, PRINCIPAL, {"from": account}, publish_source=True
    )
