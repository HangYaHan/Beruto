"""Simple portfolio manager for backtesting.

Responsibilities:
- Track cash and positions
- Apply orders (qty per symbol) with commission/slippage
- Value portfolio using latest prices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
import pandas as pd
from src.system.log import get_logger

logger = get_logger(__name__)


@dataclass
class PortfolioState:
	cash: float
	positions: Dict[str, int] = field(default_factory=dict)

	def equity(self, prices: Dict[str, float]) -> float:
		pv = sum(prices.get(sym, 0.0) * qty for sym, qty in self.positions.items())
		return self.cash + pv


class PortfolioManager:
	def __init__(self, cash: float = 1_000_000.0, commission: float = 0.0, slippage: float = 0.0) -> None:
		self.state = PortfolioState(cash=cash)
		self.commission = commission
		self.slippage = slippage

	def snapshot(self) -> PortfolioState:
		return PortfolioState(cash=self.state.cash, positions=dict(self.state.positions))

	def apply_orders(self, orders: Dict[str, int], prices: Dict[str, float]) -> None:
		"""Apply market orders at given prices.

		orders: symbol -> qty (positive buy, negative sell)
		prices: symbol -> price
		"""
		for sym, qty in orders.items():
			if qty == 0:
				continue
			px = prices.get(sym)
			if px is None:
				continue
			# apply slippage
			fill_px = px * (1 + self.slippage if qty > 0 else 1 - self.slippage)
			cost = fill_px * qty
			fee = abs(cost) * self.commission
			self.state.cash -= cost + fee
			self.state.positions[sym] = self.state.positions.get(sym, 0) + qty
			logger.info(
				"Order applied: %s side=%s qty=%s fill=%.4f cost=%.2f fee=%.2f cash=%.2f pos=%s",
				sym,
				"BUY" if qty > 0 else "SELL",
				qty,
				fill_px,
				cost,
				fee,
				self.state.cash,
				self.state.positions.get(sym),
			)

	def value(self, prices: Dict[str, float]) -> float:
		return self.state.equity(prices)


def run_backtest(strategy, data: pd.DataFrame, commission: float, slippage: float, initial_cash: float = 1_000_000.0):
	pm = PortfolioManager(cash=initial_cash, commission=commission, slippage=slippage)
	equity_curve = []

	for dt, row in data.iterrows():
		# build history up to current bar (inclusive)
		history = data.loc[:dt]
		orders = strategy.decide(dt, history)
		prices = {strategy.symbol: row['Close']}
		pm.apply_orders(orders, prices)
		equity_curve.append((dt, pm.value(prices)))

	curve_df = pd.DataFrame(equity_curve, columns=['date', 'equity']).set_index('date')
	return curve_df


__all__ = ["PortfolioManager", "run_backtest"]
