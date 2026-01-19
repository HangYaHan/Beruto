from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import copy


@dataclass
class BarData:
    """
    A single market bar for one symbol at one date.
    """
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    # Reserved for heterogeneous data like news_sentiment, etc.
    extra: Dict[str, Any]


@dataclass
class Position:
    """
    Holding state for a single symbol.
    """
    symbol: str
    volume: int        # Number of shares currently held
    avg_price: float   # Average cost per share
    last_price: float  # Latest market price used for valuation

    def market_value(self) -> float:
        """
        Return the current market value of this position.
        """
        return float(self.volume) * float(self.last_price)

    def unrealized_pnl(self) -> float:
        """
        Return the unrealized profit and loss of this position.
        """
        return (float(self.last_price) - float(self.avg_price)) * float(self.volume)


@dataclass
class AccountState:
    """
    Full account snapshot at a single time point.
    Used by the backtest engine to support time-travel (step/back).
    """
    date: datetime
    cash: float
    positions: Dict[str, Position]  # Key: symbol code
    total_assets: float             # cash + sum(position values)

    def clone(self) -> "AccountState":
        """
        Return a deep copy of this account state.
        """
        return copy.deepcopy(self)


@dataclass
class Order:
    """
    Trading instruction.
    """
    symbol: str
    volume: int                 # Positive for buy, negative for sell
    price: Optional[float]      # Expected execution price; None for market order