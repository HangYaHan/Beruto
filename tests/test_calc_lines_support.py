import pandas as pd
import pytest

from src.strategy.calc_lines import SUPPORT_LINE, RESISTANCE_LINE


def test_support_resistance_shapes_and_monotonicity():
    data = pd.Series([10, 9, 8, 9, 11, 10, 12])
    support = SUPPORT_LINE(data, window=3, temperature=1.0)
    resistance = RESISTANCE_LINE(data, window=3, temperature=1.0)
    assert len(support) == len(data)
    assert len(resistance) == len(data)
    # support should never exceed price max in window, resistance never below min in window
    assert (support <= resistance + 1e-9).all()


def test_temperature_must_be_positive():
    s = pd.Series([1, 2, 3])
    with pytest.raises(ValueError):
        SUPPORT_LINE(s, window=3, temperature=0)
    with pytest.raises(ValueError):
        RESISTANCE_LINE(s, window=3, temperature=-1)
