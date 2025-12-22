from __future__ import annotations

import pandas as pd
from typing import Dict

from src.strategy.calc_lines import CLOSE, MA, MACD, SUPPORT_LINE, RESISTANCE_LINE
from src.strategy.support import TriggerSet, crossabove, crossbelow
from src.system.log import get_logger

logger = get_logger(__name__)


class SMAStrategy:
    """
    Simple MA crossover strategy using TriggerSet to avoid global state.
    """

    def __init__(self, symbol: str, short_window: int = 5, long_window: int = 20, qty: int = 100) -> None:
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.qty = qty
        if short_window == 5:
            logger.warning("SMAStrategy: short_window uses default=5")
        if long_window == 20:
            logger.warning("SMAStrategy: long_window uses default=20")
        if qty == 100:
            logger.warning("SMAStrategy: qty uses default=100")
        self._orders: Dict[str, int] = {}
        self._triggers = TriggerSet()

        # Register triggers: buy on short crossing above long; sell on short crossing below long.
        self._triggers.always(
            lambda ctx: bool(crossabove(ctx["sma_short"], ctx["sma_long"]).iloc[-1]),
            lambda ctx: self._orders.__setitem__(self.symbol, self.qty),
            name="sma_buy_cross",
        )
        self._triggers.always(
            lambda ctx: bool(crossbelow(ctx["sma_short"], ctx["sma_long"]).iloc[-1]),
            lambda ctx: self._orders.__setitem__(self.symbol, -self.qty),
            name="sma_sell_cross",
        )

    def _select_price(self, history: pd.DataFrame) -> pd.Series | None:
        if self.symbol in history.columns:
            return CLOSE(history[[self.symbol]].rename(columns={self.symbol: "close"}))
        if "Close" in history.columns:
            return history["Close"]
        if "close" in history.columns:
            return history["close"]
        return None

    def decide(self, date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]:
        if history.empty:
            return {}

        price = self._select_price(history)
        if price is None:
            return {}

        ctx = {
            "sma_short": MA(price, self.short_window),
            "sma_long": MA(price, self.long_window),
        }

        self._orders.clear()
        self._triggers.run(ctx)
        return dict(self._orders)


class MACDStrategy:
    """MACD crossover strategy (MACD line vs signal line)."""

    def __init__(self, symbol: str, fast: int = 12, slow: int = 26, signal: int = 9, qty: int = 100) -> None:
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.qty = qty
        if fast == 12:
            logger.warning("MACDStrategy: fast uses default=12")
        if slow == 26:
            logger.warning("MACDStrategy: slow uses default=26")
        if signal == 9:
            logger.warning("MACDStrategy: signal uses default=9")
        if qty == 100:
            logger.warning("MACDStrategy: qty uses default=100")
        self._orders: Dict[str, int] = {}
        self._triggers = TriggerSet()

        self._triggers.always(
            lambda ctx: bool(crossabove(ctx["macd"], ctx["signal"]).iloc[-1]),
            lambda ctx: self._orders.__setitem__(self.symbol, self.qty),
            name="macd_buy_cross",
        )
        self._triggers.always(
            lambda ctx: bool(crossbelow(ctx["macd"], ctx["signal"]).iloc[-1]),
            lambda ctx: self._orders.__setitem__(self.symbol, -self.qty),
            name="macd_sell_cross",
        )

    def _select_price(self, history: pd.DataFrame) -> pd.Series | None:
        if self.symbol in history.columns:
            return CLOSE(history[[self.symbol]].rename(columns={self.symbol: "close"}))
        if "Close" in history.columns:
            return history["Close"]
        if "close" in history.columns:
            return history["close"]
        return None

    def decide(self, date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]:
        if history.empty:
            return {}

        price = self._select_price(history)
        if price is None:
            return {}

        macd_df = MACD(price, fast=self.fast, slow=self.slow, signal=self.signal)
        ctx = {
            "macd": macd_df["macd"],
            "signal": macd_df["signal"],
        }

        self._orders.clear()
        self._triggers.run(ctx)
        return dict(self._orders)


class MACDMonotoneStrategy:
    """MACD variant: 3-bar monotone moves with size scaled by distance from zero."""

    def __init__(
        self,
        symbol: str,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        base_qty: int = 100,
        sensitivity: float = 10.0,
        max_multiplier: float = 3.0,
    ) -> None:
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.base_qty = base_qty
        self.sensitivity = sensitivity
        self.max_multiplier = max_multiplier
        if fast == 12:
            logger.warning("MACDMonotoneStrategy: fast uses default=12")
        if slow == 26:
            logger.warning("MACDMonotoneStrategy: slow uses default=26")
        if signal == 9:
            logger.warning("MACDMonotoneStrategy: signal uses default=9")
        if base_qty == 100:
            logger.warning("MACDMonotoneStrategy: base_qty uses default=100")
        if sensitivity == 10.0:
            logger.warning("MACDMonotoneStrategy: sensitivity uses default=10.0")
        if max_multiplier == 3.0:
            logger.warning("MACDMonotoneStrategy: max_multiplier uses default=3.0")

    def _select_price(self, history: pd.DataFrame) -> pd.Series | None:
        if self.symbol in history.columns:
            return CLOSE(history[[self.symbol]].rename(columns={self.symbol: "close"}))
        if "Close" in history.columns:
            return history["Close"]
        if "close" in history.columns:
            return history["close"]
        return None

    def _is_monotone(self, series: pd.Series, direction: str) -> bool:
        if series.shape[0] < 3:
            return False
        window = series.iloc[-3:]
        if window.isna().any():
            return False
        if direction == "up":
            return bool(window.iloc[0] < window.iloc[1] < window.iloc[2])
        if direction == "down":
            return bool(window.iloc[0] > window.iloc[1] > window.iloc[2])
        raise ValueError(f"Unknown direction: {direction}")

    def _scaled_qty(self, macd_value: float, side: str) -> int:
        distance = -macd_value if side == "buy" else macd_value
        distance = max(distance, 0.0)
        multiplier = 1 + self.sensitivity * distance
        if self.max_multiplier is not None:
            multiplier = min(multiplier, self.max_multiplier)
        qty = int(self.base_qty * multiplier)
        return max(qty, 0)

    def decide(self, date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]:
        if history.empty:
            return {}

        price = self._select_price(history)
        if price is None:
            return {}

        macd_series = MACD(price, fast=self.fast, slow=self.slow, signal=self.signal)["macd"]

        if self._is_monotone(macd_series, "up"):
            qty = self._scaled_qty(macd_series.iloc[-1], side="buy")
            return {self.symbol: qty} if qty > 0 else {}

        if self._is_monotone(macd_series, "down"):
            qty = self._scaled_qty(macd_series.iloc[-1], side="sell")
            return {self.symbol: -qty} if qty > 0 else {}

        return {}


class BuyAndHoldStrategy:
    """Use initial cash to buy as many shares as possible on the first bar, then hold."""

    def __init__(self, symbol: str, initial_cash: float = 1_000_000.0, commission: float = 0.0, slippage: float = 0.0) -> None:
        self.symbol = symbol
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage
        self._bought = False
        if initial_cash == 1_000_000.0:
            logger.warning("BuyAndHoldStrategy: initial_cash uses default=1_000_000")
        if commission == 0.0:
            logger.warning("BuyAndHoldStrategy: commission uses default=0")
        if slippage == 0.0:
            logger.warning("BuyAndHoldStrategy: slippage uses default=0")

    def decide(self, date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]:
        if self._bought or history.empty:
            return {}

        # Use the latest close (first bar when called) to size maximum purchasable shares
        if self.symbol in history.columns:
            px = CLOSE(history[[self.symbol]].rename(columns={self.symbol: "close"})).iloc[-1]
        elif "Close" in history.columns:
            px = history["Close"].iloc[-1]
        elif "close" in history.columns:
            px = history["close"].iloc[-1]
        else:
            return {}

        effective_price = px * (1 + self.slippage) * (1 + self.commission)
        if effective_price <= 0:
            return {}

        qty = int(self.initial_cash // effective_price)
        if qty <= 0:
            return {}

        self._bought = True
        return {self.symbol: qty}


class SupportResistanceStrategy:
    """Breakout above smoothed resistance; exit on support breakdown.

    Temperature controls smoothing strength for support/resistance lines.
    """

    def __init__(self, symbol: str, window: int = 20, temperature: float = 1.0, qty: int = 100) -> None:
        self.symbol = symbol
        self.window = window
        self.temperature = temperature
        self.qty = qty
        if window == 20:
            logger.warning("SupportBreakoutStrategy: window uses default=20")
        if temperature == 1.0:
            logger.warning("SupportBreakoutStrategy: temperature uses default=1.0")
        if qty == 100:
            logger.warning("SupportBreakoutStrategy: qty uses default=100")
        self._orders: Dict[str, int] = {}
        self._triggers = TriggerSet()

        self._triggers.always(
            lambda ctx: bool(crossabove(ctx["close"], ctx["resistance"]).iloc[-1]),
            lambda ctx: self._orders.__setitem__(self.symbol, self.qty),
            name="breakout_buy",
        )
        self._triggers.always(
            lambda ctx: bool(crossbelow(ctx["close"], ctx["support"]).iloc[-1]),
            lambda ctx: self._orders.__setitem__(self.symbol, -self.qty),
            name="support_exit",
        )

    def _select_price(self, history: pd.DataFrame) -> pd.Series | None:
        if self.symbol in history.columns:
            return CLOSE(history[[self.symbol]].rename(columns={self.symbol: "close"}))
        if "Close" in history.columns:
            return history["Close"]
        if "close" in history.columns:
            return history["close"]
        return None

    def decide(self, date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]:
        if history.empty:
            return {}

        price = self._select_price(history)
        if price is None:
            return {}

        try:
            support = SUPPORT_LINE(price, window=self.window, temperature=self.temperature)
            resistance = RESISTANCE_LINE(price, window=self.window, temperature=self.temperature)
        except Exception:
            logger.exception("Failed to compute support/resistance")
            return {}

        ctx = {
            "close": price,
            "support": support,
            "resistance": resistance,
        }

        self._orders.clear()
        self._triggers.run(ctx)
        return dict(self._orders)