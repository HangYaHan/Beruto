"""
Common indicator interfaces (function signatures only).
Implementations can use pandas/numpy.
"""
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average (SMA) interface."""
    pass


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential moving average (EMA) interface."""
    pass