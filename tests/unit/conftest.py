import pytest
from brownie import accounts, Ownable


@pytest.fixture(scope="session")
def deployer(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def user(accounts):
    yield accounts[1]


@pytest.fixture(scope="module")
def ownable(deployer):
    yield Ownable.deploy({"from": deployer})
