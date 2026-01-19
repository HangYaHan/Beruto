from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.backtest.datatype import BarData


class DataProxy:
    """
    Data access layer.
    Prevents look-ahead bias by restricting reads to the current date.
    Factors must obtain market data via this proxy.
    """

    def __init__(self, universe: List[str], start_date: datetime, end_date: datetime, data_dir: Optional[Path] = None) -> None:
        self._universe = list(universe)
        self._start_date = start_date
        self._end_date = end_date
        self._current_date = start_date
        
        # Project root is two levels up from this file (src/backtest)
        self._data_dir = data_dir or Path(__file__).resolve().parents[2] / "data" / "kline"
        self._frames: Dict[str, pd.DataFrame] = {}
        self._calendar: List[datetime] = []
        self._load_all()

    def _load_all(self) -> None:
        dates: set[datetime] = set()
        for code in self._universe:
            df = self._load_symbol(code)
            if df is None:
                df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])  # empty
            # Filter by range
            if not df.empty:
                df = df[(df["date"] >= self._start_date) & (df["date"] <= self._end_date)].copy()
            self._frames[code] = df.reset_index(drop=True)
            if not df.empty:
                for d in df["date"].unique():
                    dates.add(pd.to_datetime(d).to_pydatetime())
        self._calendar = sorted(dates)
        if self._calendar:
            self._current_date = self._calendar[0]

    def _load_symbol(self, code: str) -> Optional[pd.DataFrame]:
        path = self._data_dir / f"{code}.csv"
        if not path.exists():
            return None
        try:
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            # Ensure numeric
            for col in ("open", "high", "low", "close", "volume"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        except Exception:
            return None

    def available_dates(self) -> List[datetime]:
        return list(self._calendar)

    def on_date_change(self, new_date: datetime) -> None:
        """
        Update internal pointer; subsequent reads are limited to new_date or earlier.
        """
        self._current_date = new_date

    def _latest_row(self, code: str) -> Optional[pd.Series]:
        df = self._frames.get(code)
        if df is None or df.empty:
            return None
        df2 = df[df["date"] <= self._current_date]
        if df2.empty:
            return None
        return df2.iloc[-1]

    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        row = self._latest_row(symbol)
        if row is None:
            return None
        return BarData(
            symbol=symbol,
            date=pd.to_datetime(row["date"]).to_pydatetime(),
            open=float(row.get("open", float("nan"))),
            high=float(row.get("high", float("nan"))),
            low=float(row.get("low", float("nan"))),
            close=float(row.get("close", float("nan"))),
            volume=float(row.get("volume", 0.0)),
            extra={},
        )

    def get_history(self, symbol: str, n: int) -> List[BarData]:
        df = self._frames.get(symbol)
        if df is None or df.empty:
            return []
        df2 = df[df["date"] <= self._current_date]
        if df2.empty:
            return []
        tail = df2.tail(int(n))
        out: List[BarData] = []
        for _, row in tail.iterrows():
            out.append(
                BarData(
                    symbol=symbol,
                    date=pd.to_datetime(row["date"]).to_pydatetime(),
                    open=float(row.get("open", float("nan"))),
                    high=float(row.get("high", float("nan"))),
                    low=float(row.get("low", float("nan"))),
                    close=float(row.get("close", float("nan"))),
                    volume=float(row.get("volume", 0.0)),
                    extra={},
                )
            )
        return out
