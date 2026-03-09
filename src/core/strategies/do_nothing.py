from __future__ import annotations

from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction
from core.strategy_base import Strategy


class DoNothingStrategy(Strategy):
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        return TradeAction(
            asof=pd.Timestamp(asof),
            action="HOLD",
            ratio=0.0,
            reason="No action strategy.",
            metrics={},
        )
