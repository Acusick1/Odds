import pytest
import numpy as np
from utils import probability


ODDS = np.array([1/100, 1/3, 1, 4, 20, 200])
PROBS = np.array([.99, .75, .5, .2, .048, .005])


def test_odds2probs():

    probs = probability.odds2probs(ODDS)
    np.testing.assert_almost_equal(probs, PROBS, decimal=3)


def test_probs2odds():

    odds = probability.probs2odds(PROBS)
    np.testing.assert_almost_equal(odds, ODDS, decimal=0)


@pytest.mark.parametrize(
    "r1, r2, actual",
    [
        (10/3, 13/5, 10/11),
        (13/5, 5/6, 1/5),
        (5/6, 10/3, 2/7)
    ]
)
def test_combined_odds(r1, r2, actual):

    combined = probability.combined_odds(np.array([r1, r2]))
    np.testing.assert_almost_equal(combined, actual, decimal=1)
