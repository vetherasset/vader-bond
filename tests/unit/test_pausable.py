import brownie


def test_pause(pausable, deployer):
    tx = pausable.pause({"from": deployer})

    assert pausable.paused()

    assert len(tx.events) == 1
    assert tx.events["Pause"].values() == [True]

    with brownie.reverts("paused"):
        pausable.pause({"from": deployer})


def test_pause(pausable, deployer):
    with brownie.reverts("not paused"):
        pausable.unpause({"from": deployer})

    pausable.pause()

    tx = pausable.unpause({"from": deployer})

    assert not pausable.paused()

    assert len(tx.events) == 1
    assert tx.events["Pause"].values() == [False]
