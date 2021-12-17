import os
import pytest
from brownie import interface


@pytest.fixture(scope="session")
def deployer(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def user(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def vader():
    yield interface.IERC20("0x2602278EE1882889B946eb11DC0E810075650983")


# ETH VADER LP
@pytest.fixture(scope="session")
def lp():
    yield interface.IERC20("0x452c60e1E3Ae0965Cd27dB1c7b3A525d197Ca0Aa")


@pytest.fixture(scope="session")
def vader_whale(accounts):
    yield accounts.at(os.getenv("VADER_WHALE"), force=True)
