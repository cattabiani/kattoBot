from src import dice
import numpy as np


def test_roll_ndm():
    for i in range(10):
        l = dice.roll_ndm(10, 4)
        assert len(l) == 10
        assert np.array_equal(l, sorted(l, reverse=True))
        assert all(i >= 1 for i in l)
        assert all(i <= 4 for i in l)


def test_roll_ndm_no_dice():
    l = dice.roll_ndm(0, 4)
    assert len(l) == 0


def test_roll_ndm_with_successes():
    for i in range(10):
        l = dice.roll_ndm(7, 10, True)
        assert l.count(10) + 7 == len(l)
        assert np.array_equal(l, sorted(l, reverse=True))
        assert all(i >= 1 for i in l)
        assert all(i <= 10 for i in l)
