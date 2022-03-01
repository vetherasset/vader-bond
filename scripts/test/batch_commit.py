from brownie import TestToken, PreCommit, accounts, network

MAX_COMMITS = 100
N = 30
AMOUNT = 0.01 * 10 ** 18

CONTRACTS = {
    "pre_commit": "0x795bE6b0BF54AF587385604B9DB869E797db69E0",
    "token": "0xE8bD273f54a990007b1069a15b66B584abc86e04",
}


def main():
    account = accounts.load("dev")
    print(f"account: {account}")

    net = network.show_active()
    assert net in ["rinkeby"]

    preCommit = PreCommit.at(CONTRACTS["pre_commit"])
    count = preCommit.count()
    assert MAX_COMMITS - count >= N

    token = TestToken.at(CONTRACTS["token"])
    # check token balance and approval of account
    assert token.balanceOf(account) >= N * AMOUNT
    assert token.allowance(account, preCommit) >= N * AMOUNT

    for i in range(N):
        print(i)
        preCommit.commit(AMOUNT, {"from": account})
