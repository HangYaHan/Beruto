from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.backtest.datatype import AccountState


class Context:
    """
    Runtime context containing the current date, account state,
    and a data proxy to fetch market data for factors and engine.
    """

    def __init__(self, current_date: datetime, account: AccountState, data_proxy: "DataProxy") -> None:
        self.current_date = current_date
        self.account = account
        self.data_proxy = data_proxy

    def history(self, symbol: str, count: int) -> pd.DataFrame:
        """
        Convenience wrapper to get the last N bars up to current date as a DataFrame.
        """
        bars = self.data_proxy.get_history(symbol, count)
        if not bars:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])  # empty
        return pd.DataFrame(
            [{
                "date": b.date,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            } for b in bars]
        )

    def snapshot(self) -> AccountState:
        """
        Return a deep copy of the current account state (for history persistence).
        """
        return self.account.clone()
