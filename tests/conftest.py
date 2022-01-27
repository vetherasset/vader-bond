import pytest
from brownie import (
    accounts,
    Ownable,
    Treasury,
    VaderBond,
    ZapUniswapV2EthLp,
    TestPausable,
    TestToken,
    TestVader,
    MockRouter,
    MockPair,
)


@pytest.fixture(scope="session")
def deployer(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def user(accounts):
    yield accounts[1]


# treasury withdraw destination
@pytest.fixture(scope="session")
def dest(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def ownable(deployer):
    yield Ownable.deploy({"from": deployer})


@pytest.fixture(scope="module")
def pausable(deployer):
    yield TestPausable.deploy({"from": deployer})


@pytest.fixture(scope="module")
def treasury(deployer, payoutToken):
    yield Treasury.deploy(payoutToken, {"from": deployer})


@pytest.fixture(scope="module")
def bond(deployer, treasury, payoutToken, principalToken):
    yield VaderBond.deploy(treasury, payoutToken, principalToken, {"from": deployer})


WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"


@pytest.fixture(scope="module")
def zapUniswapV2EthLp(deployer, router, pair, payoutToken, bond):
    yield ZapUniswapV2EthLp.deploy(
        WETH, router, pair, payoutToken, bond, {"from": deployer}
    )


# test contracts
@pytest.fixture(scope="module")
def payoutToken(deployer):
    yield TestVader.deploy({"from": deployer})


@pytest.fixture(scope="module")
def principalToken(deployer):
    yield TestToken.deploy("PRINCIPAL TOKEN", "PRINCIPAL", 18, {"from": deployer})


# alias
@pytest.fixture(scope="module")
def vader(payoutToken):
    yield payoutToken


@pytest.fixture(scope="module")
def pair(deployer):
    yield MockPair.deploy({"from": deployer})


@pytest.fixture(scope="module")
def router(deployer, pair):
    yield MockRouter.deploy(pair, {"from": deployer})
