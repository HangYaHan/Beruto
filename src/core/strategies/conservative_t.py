from __future__ import annotations

from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction
from core.strategy_base import Strategy


class ConservativeTStrategy(Strategy):
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        x_pct = float(params.get("x_pct", 0.02))
        y_pct = float(params.get("y_pct", 0.1))
        recent_trade_in_5 = bool(params.get("recent_trade_in_5", False))

        if len(bars) < 2 or not recent_trade_in_5:
            return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No recent trade in last 5 bars.")

        prev_close = float(bars["close"].iloc[-2])
        latest_close = float(bars["close"].iloc[-1])
        if prev_close <= 0:
            return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "Invalid previous close.")

        change = latest_close / prev_close - 1.0
        if change >= x_pct and position.shares > 0:
            return TradeAction(
                asof=pd.Timestamp(asof),
                action="SELL",
                ratio=y_pct,
                reason="Conservative-T: up move trigger sell.",
                metrics={"change": change, "x_pct": x_pct, "y_pct": y_pct},
            )
        if change <= -x_pct and position.shares > 0:
            return TradeAction(
                asof=pd.Timestamp(asof),
                action="BUY",
                ratio=y_pct,
                reason="Conservative-T: down move trigger buy.",
                metrics={"change": change, "x_pct": x_pct, "y_pct": y_pct},
            )

        return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No conservative-T trigger.")
