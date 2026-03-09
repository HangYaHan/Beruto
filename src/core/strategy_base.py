from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from core.models import PositionState, TradeAction


class Strategy(ABC):
    @abstractmethod
    def generate_action(
        self,
        bars: pd.DataFrame,
        asof: pd.Timestamp,
        position: PositionState,
        params: dict[str, Any],
    ) -> TradeAction:
        """Return a trade action for one symbol at the current rebalance time."""
