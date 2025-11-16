"""
Strategy base interface definitions.
- lifecycle methods (on_start/on_stop)
- market data callbacks (on_bar/on_tick)
- signal generation interface
"""
from typing import Any
import pandas as pd


class Strategy:
    def __init__(self, config: dict):
        """Initialize strategy instance (accepts a config dict)."""
        self.config = config

    def on_start(self) -> None:
        """Strategy start callback (initialize internal state)."""
        pass

    def on_stop(self) -> None:
        """Strategy stop callback (cleanup resources)."""
        pass

    def on_bar(self, bar: pd.Series) -> None:
        """Receive a bar (or aggregated data)."""
        pass

    def on_tick(self, tick: Any) -> None:
        """Receive tick-level market data."""
        pass

    def generate_signals(self) -> Any:
        """Return a signals object (to be parsed into orders by the framework)."""
        pass