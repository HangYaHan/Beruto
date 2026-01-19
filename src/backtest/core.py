from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from src.backtest.context import Context
from src.backtest.feed import DataProxy
from src.backtest.datatype import AccountState, Position
from src.factors.base import Factor
from src.factors.Do_Nothing import Do_Nothing


class BacktestEngine:
    """
    Backtest orchestrator.
    """

    def __init__(self, config: Dict) -> None:
        """
        Initialize from JSON-like config:
        1) Load data via DataProxy
        2) Initialize AccountState (initial cash)
        3) Instantiate Factors
        """
        universe: List[str] = config.get("symbols") or config.get("Universe", {}).get("symbols", [])
        if not universe:
            raise ValueError("Config requires a non-empty symbol universe.")

        sd_str: Optional[str] = config.get("start_date") or config.get("Universe", {}).get("start_date")
        ed_str: Optional[str] = config.get("end_date") or config.get("Universe", {}).get("end_date")
        if not sd_str or not ed_str:
            raise ValueError("Config requires start_date and end_date.")
        start_date = datetime.fromisoformat(sd_str)
        end_date = datetime.fromisoformat(ed_str)

        initial_cash: float = float(
            config.get("initial_cash")
            or config.get("Executor", {}).get("initial_cash", 1_000_000.0)
        )

        self._data = DataProxy(universe=universe, start_date=start_date, end_date=end_date)
        self._calendar: List[datetime] = self._data.available_dates()
        if not self._calendar:
            raise RuntimeError("No trading dates available in data range.")

        # Account and context
        self._account = AccountState(
            date=self._calendar[0], cash=initial_cash, positions={}, total_assets=initial_cash
        )
        self._context = Context(current_date=self._calendar[0], account=self._account, data_proxy=self._data)

        # Factors (placeholder pipeline)
        self._factors: List[Factor] = [Do_Nothing(params={})]

        # History and pointer
        self._history_states: List[AccountState] = []
        self._current_index: int = -1

    def _mark_to_market(self) -> None:
        """
        Update positions' last_price and recompute total assets.
        """
        total = float(self._context.account.cash)
        for code, pos in list(self._context.account.positions.items()):
            bar = self._data.get_latest_bar(code)
            if bar is None:
                continue
            pos.last_price = float(bar.close)
            total += pos.market_value()
        self._context.account.total_assets = total

    def _aggregate_target_weights(self) -> Dict[str, float]:
        """
        Aggregate factor opinions into target weights; simple average across factors.
        Factors may return None to indicate no opinion.
        """
        out: Dict[str, float] = {}
        for code in self._data._universe:  # using internal universe for now
            votes: List[float] = []
            for f in self._factors:
                try:
                    w = f.calculate(self._context, code)
                except Exception:
                    w = None
                if w is not None:
                    votes.append(float(w))
            if votes:
                out[code] = sum(votes) / len(votes)
        return out

    def step(self) -> AccountState:
        """
        Advance one trading day and return the new snapshot.
        """
        if self._current_index + 1 >= len(self._calendar):
            raise StopIteration("Already at the end of calendar.")
        self._current_index += 1
        new_date = self._calendar[self._current_index]
        self._context.current_date = new_date
        self._data.on_date_change(new_date)

        # Mark to market existing positions
        self._mark_to_market()

        # TODO: generate orders from target weights; placeholder keeps positions unchanged
        _ = self._aggregate_target_weights()
        # Order execution, fees, and constraints can be added here

        # Snapshot and persist
        snapshot = self._context.snapshot()
        self._history_states.append(snapshot)
        return snapshot

    def back(self) -> AccountState:
        """
        Step back one day, restoring context and returning the state.
        """
        if self._current_index <= 0:
            raise StopIteration("Already at the beginning of calendar.")
        self._current_index -= 1
        state = self._history_states[self._current_index]
        self._context.account = state.clone()
        self._context.current_date = state.date
        self._data.on_date_change(state.date)
        # Drop the last snapshot beyond current index
        self._history_states = self._history_states[: self._current_index + 1]
        return state

    def run_to_end(self) -> List[AccountState]:
        """
        Convenience method: step until final date.
        """
        snapshots: List[AccountState] = []
        while self._current_index + 1 < len(self._calendar):
            snapshots.append(self.step())
        return snapshots
