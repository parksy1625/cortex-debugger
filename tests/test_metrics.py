import math

import pytest

from cortex_engine.metrics import logit_margin, recovery_score


def test_margin():
    assert logit_margin(2.5, -1.0) == 3.5


def test_recovery_half():
    assert recovery_score(4.0, 0.0, 2.0) == 0.5


def test_recovery_is_not_clamped():
    assert recovery_score(4.0, 0.0, 8.0) == 2.0
    assert recovery_score(4.0, 0.0, -1.0) == -0.25


def test_zero_denominator_is_undefined():
    assert recovery_score(2.0, 2.0, 2.0) is None
    assert recovery_score(2.0 + 1e-10, 2.0, 2.0) is None


def test_reject_nonfinite():
    with pytest.raises(ValueError):
        logit_margin(math.inf, 2.0)
    with pytest.raises(ValueError):
        recovery_score(2.0, 1.0, math.nan)


def test_reject_invalid_epsilon():
    with pytest.raises(ValueError):
        recovery_score(2.0, 1.0, 1.0, epsilon=-1.0)
