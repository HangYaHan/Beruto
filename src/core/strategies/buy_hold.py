from __future__ import annotations

from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction
from core.strategy_base import Strategy


class BuyHoldStrategy(Strategy):
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        if position.shares <= 0:
            return TradeAction(
                asof=pd.Timestamp(asof),
                action="BUY",
                ratio=1.0,
                reason="No shares held; buy signal from buy-hold strategy.",
                metrics={},
            )

        return TradeAction(
            asof=pd.Timestamp(asof),
            action="HOLD",
            ratio=0.0,
            reason="Buy-hold keeps position unchanged.",
            metrics={},
        )
