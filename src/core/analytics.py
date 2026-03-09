from __future__ import annotations

import numpy as np
import pandas as pd


def compute_max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def summarize_performance(daily_returns: pd.Series, equity: pd.Series) -> dict[str, float]:
    if daily_returns.empty or equity.empty:
        return {
            "cumulative_return": 0.0,
            "max_drawdown": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe": 0.0,
        }

    cumulative_return = float(equity.iloc[-1] - 1.0)
    max_drawdown = compute_max_drawdown(equity)

    n = len(daily_returns)
    annualized_return = float((1.0 + cumulative_return) ** (252 / max(n, 1)) - 1.0)
    annualized_volatility = float(daily_returns.std(ddof=0) * np.sqrt(252))
    sharpe = (
        float(daily_returns.mean() / daily_returns.std(ddof=0) * np.sqrt(252))
        if daily_returns.std(ddof=0) > 0
        else 0.0
    )

    return {
        "cumulative_return": cumulative_return,
        "max_drawdown": max_drawdown,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe": sharpe,
    }
