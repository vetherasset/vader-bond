import pytest
from brownie import (
    accounts,
    Ownable,
    Treasury,
    VaderBond,
    PreCommit,
    ZapEthToPreCommit,
    ZapUniswapV2EthLp,
    WETH,
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


@pytest.fixture(scope="module")
def preCommit(deployer, bond, principalToken):
    yield PreCommit.deploy(
        bond,
        principalToken,
        {"from": deployer},
    )


@pytest.fixture(scope="module")
def preCommitWeth(deployer, bond, weth):
    preCommit = PreCommit.deploy(
        bond,
        weth,
        {"from": deployer},
    )

    max_commits = 50
    min_amount_in = int(0.01 * 10 ** 18)
    max_amount_in = int(10 * 10 ** 18)

    preCommit.start(max_commits, min_amount_in, max_amount_in, {"from": deployer})

    yield preCommit


@pytest.fixture(scope="module")
def zapEthToPreCommit(deployer, weth, preCommitWeth):
    yield ZapEthToPreCommit.deploy(weth, preCommitWeth, {"from": deployer})


@pytest.fixture(scope="module")
def zapUniswapV2EthLp(deployer, router, pair, payoutToken, bond):
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
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


@pytest.fixture(scope="module")
def weth(deployer):
    yield WETH.deploy({"from": deployer})


# alias
@pytest.fixture(scope="module")
def vader(payoutToken):
    yield payoutToken


@pytest.fixture(scope="module")
def tokenIn(principalToken):
    yield principalToken


@pytest.fixture(scope="module")
def pair(deployer):
    yield MockPair.deploy({"from": deployer})


@pytest.fixture(scope="module")
def router(deployer, pair):
    yield MockRouter.deploy(pair, {"from": deployer})
