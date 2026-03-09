from __future__ import annotations

from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction
from core.strategy_base import Strategy


class AddOnFiveDownStrategy(Strategy):
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        x_pct = float(params.get("x_pct", 0.01))
        y_pct = float(params.get("y_pct", 0.1))

        if position.shares <= 0 or len(bars) < 6:
            return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No position or insufficient bars.")

        closes = bars["close"].astype(float)
        recent5 = closes.iloc[-5:]
        prev5 = closes.iloc[-6:-1]
        latest = float(closes.iloc[-1])

        monotonic_decrease = all(float(recent5.iloc[i]) < float(recent5.iloc[i - 1]) for i in range(1, 5))
        prev5_min = float(prev5.min())

        if monotonic_decrease and prev5_min > 0 and latest <= prev5_min * (1.0 - x_pct):
            return TradeAction(
                asof=pd.Timestamp(asof),
                action="BUY",
                ratio=y_pct,
                reason="Five-day monotonic decline and breakdown trigger add-on.",
                metrics={"latest_close": latest, "prev5_min": prev5_min, "x_pct": x_pct, "y_pct": y_pct},
            )

        return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No add-on trigger.")
