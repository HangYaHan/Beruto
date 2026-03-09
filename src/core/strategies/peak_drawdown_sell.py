from __future__ import annotations

from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction
from core.strategy_base import Strategy


class PeakDrawdownSellStrategy(Strategy):
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        x_pct = float(params.get("x_pct", 0.03))
        y_pct = float(params.get("y_pct", 0.2))

        if position.shares <= 0 or len(bars) < 5:
            return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No position or insufficient bars.")

        recent = bars["close"].tail(5).astype(float)
        latest = float(recent.iloc[-1])
        peak = float(recent.max())

        if peak > 0 and latest <= peak * (1.0 - x_pct):
            return TradeAction(
                asof=pd.Timestamp(asof),
                action="SELL",
                ratio=y_pct,
                reason="Close dropped below rolling-5 peak threshold.",
                metrics={"latest_close": latest, "peak_5": peak, "x_pct": x_pct, "y_pct": y_pct},
            )

        return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No peak drawdown trigger.")
