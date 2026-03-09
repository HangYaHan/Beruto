from __future__ import annotations

from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction
from core.strategy_base import Strategy


class TakeProfitRetraceStrategy(Strategy):
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        x_pct = float(params.get("x_pct", 0.08))
        y_pct = float(params.get("y_pct", 0.2))

        if position.shares <= 0 or position.avg_buy_price <= 0 or bars.empty:
            return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No position or no average buy price.")

        latest = float(bars["close"].iloc[-1])
        if latest >= position.avg_buy_price * (1.0 + x_pct):
            return TradeAction(
                asof=pd.Timestamp(asof),
                action="SELL",
                ratio=y_pct,
                reason="Take-profit threshold reached.",
                metrics={
                    "latest_close": latest,
                    "avg_buy_price": position.avg_buy_price,
                    "x_pct": x_pct,
                    "y_pct": y_pct,
                },
            )

        return TradeAction(pd.Timestamp(asof), "HOLD", 0.0, "No take-profit trigger.")
