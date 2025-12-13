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

	def apply_orders(self, orders: Dict[str, int], prices: Dict[str, float]):
		"""Apply market orders at given prices.

		orders: symbol -> qty (positive buy, negative sell)
		prices: symbol -> price
		"""
		fills = []
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
			fills.append({"symbol": sym, "qty": qty, "price": fill_px, "fee": fee, "side": "BUY" if qty>0 else "SELL"})
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
		return fills
	def value(self, prices: Dict[str, float]) -> float:
		return self.state.equity(prices)


def run_backtest(strategy, data: pd.DataFrame, commission: float, slippage: float, initial_cash: float = 1_000_000.0):
	pm = PortfolioManager(cash=initial_cash, commission=commission, slippage=slippage)
	records = []
	fills_records = []

	for dt, row in data.iterrows():
		# build history up to current bar (inclusive)
		history = data.loc[:dt]
		orders = strategy.decide(dt, history)
		prices = {strategy.symbol: row['Close']}
		fills = pm.apply_orders(orders, prices)
		# record fills with timestamp
		for f in fills:
			fills_records.append({"date": dt, **f})
		# breakdown values
		px = prices.get(strategy.symbol, 0.0)
		pos_qty = pm.state.positions.get(strategy.symbol, 0)
		position_value = pos_qty * px
		equity = pm.state.cash + position_value
		records.append((dt, equity, pm.state.cash, position_value))

	curve_df = pd.DataFrame(records, columns=['date', 'equity', 'cash', 'position_value']).set_index('date')
	# stock part return: pct change of position_value; when previous value is 0, define 0
	curve_df['stock_return_pct'] = curve_df['position_value'].pct_change().fillna(0.0).replace([pd.NA, pd.NaT], 0.0)
	return curve_df, pd.DataFrame(fills_records)


__all__ = ["PortfolioManager", "run_backtest"]
