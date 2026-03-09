from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class TradeAction:
    asof: pd.Timestamp
    action: str  # BUY/SELL/HOLD
    ratio: float
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.ratio = float(min(1.0, max(0.0, self.ratio)))
        if self.action not in {"BUY", "SELL", "HOLD"}:
            raise ValueError(f"Unsupported action: {self.action}")


@dataclass
class StrategySpec:
    name: str
    x_pct: float = 0.0
    y_pct: float = 0.0


@dataclass
class SymbolSpec:
    symbol: str
    weight: float
    strategies: list[StrategySpec] = field(default_factory=list)


@dataclass
class PortfolioConfig:
    initial_cash: float
    fee_rate: float
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    symbols: list[SymbolSpec] = field(default_factory=list)


@dataclass
class PositionState:
    shares: float = 0.0
    avg_buy_price: float = 0.0
    trade_dates: list[pd.Timestamp] = field(default_factory=list)


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    daily_returns: pd.Series
    signals: pd.DataFrame
    metrics: dict[str, Any]
    notes: list[str] = field(default_factory=list)
