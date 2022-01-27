from brownie import ZapUniswapV2EthLp, accounts, network
import os

CONTRACTS = {
    "kovan": {
        "weth": "0xd0A1E359811322d97991E03f863a0C30C2cF029C",
        "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "pair": "0xC42706E83433580dd8d865a30e2Ae61082056007",
        "vader": "0xB46dbd07ce34813623FB0643b21DCC8D0268107D",
        "bond": "0xd932cc11F49df7638999E2a313e5808667363750",
    },
    "mainnet": {
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "pair": "0x452c60e1E3Ae0965Cd27dB1c7b3A525d197Ca0Aa",
        "vader": "0x2602278EE1882889B946eb11DC0E810075650983",
        "bond": "0x1B96d82b8b13C75d4cE347a53284B10d93B63684",
    },
}


def main():
    account = accounts.load(os.getenv("ACCOUNT"))
    print(f"account: {account}")

    net = network.show_active()
    contracts = CONTRACTS[net]

    ZapUniswapV2EthLp.deploy(
        contracts["weth"],
        contracts["router"],
        contracts["pair"],
        contracts["vader"],
        contracts["bond"],
        {"from": account},
        publish_source=True,
    )
