import pandas as pd
import pytest

from src.strategy.support import drawdown, take_profit


def test_drawdown_edges_only():
    returns = pd.Series([0.0, -0.02, -0.06, -0.06, -0.04])
    triggered = drawdown(returns, 0.05)
    assert triggered.tolist() == [False, False, True, False, False]


def test_take_profit_edges_only():
    returns = pd.Series([0.0, 0.03, 0.08, 0.06, 0.09])
    triggered = take_profit(returns, 0.07)
    assert triggered.tolist() == [False, False, True, False, False]


def test_never_flag_disables_signals():
    returns = pd.Series([0.1, -0.2, 0.3])
    assert drawdown(returns, 0.05, never=True).eq(False).all()
    assert take_profit(returns, 0.05, never=True).eq(False).all()


def test_threshold_must_be_positive():
    returns = pd.Series([0.0, 0.01])
    with pytest.raises(ValueError):
        drawdown(returns, 0)
    with pytest.raises(ValueError):
        take_profit(returns, -0.01)
