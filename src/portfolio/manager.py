"""Simple portfolio manager for backtesting.

Responsibilities:
- Track cash and positions
- Apply orders (qty per symbol) with commission/slippage
- Value portfolio using latest prices
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Iterable
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
	def __init__(
		self,
		cash: float = 1_000_000.0,
		commission: float = 0.0,
		slippage: float = 0.0,
		allow_short: bool = True,
		initial_positions: Dict[str, int] | None = None,
	) -> None:
		self.state = PortfolioState(cash=cash, positions=dict(initial_positions or {}))
		self.commission = commission
		self.slippage = slippage
		self.allow_short = allow_short

	def snapshot(self) -> PortfolioState:
		return PortfolioState(cash=self.state.cash, positions=dict(self.state.positions))

	def apply_orders(self, orders: Dict[str, int], prices: Dict[str, float], *, strategy_name: str | None = None):
		"""Apply market orders at given prices.

		orders: symbol -> qty (positive buy, negative sell)
		prices: symbol -> price
		"""
		fills: List[Dict[str, float | int | str]] = []
		for sym, qty in orders.items():
			if qty == 0:
				continue
			px = prices.get(sym)
			if px is None:
				continue
			current_pos = self.state.positions.get(sym, 0)
			# If short not allowed, cap sells to available position
			if not self.allow_short and current_pos + qty < 0:
				qty = -current_pos
				if qty == 0:
					continue
			# apply slippage
			fill_px = px * (1 + self.slippage if qty > 0 else 1 - self.slippage)
			cost = fill_px * qty
			fee = abs(cost) * self.commission
			self.state.cash -= cost + fee
			self.state.positions[sym] = self.state.positions.get(sym, 0) + qty
			fills.append({
				"symbol": sym,
				"qty": qty,
				"price": fill_px,
				"fee": fee,
				"side": "BUY" if qty > 0 else "SELL",
				"strategy": strategy_name or "",
			})
		return fills
	def value(self, prices: Dict[str, float]) -> float:
		return self.state.equity(prices)

def _union_sorted_indices(frames: Iterable[pd.DataFrame]) -> List[pd.Timestamp]:
	idx = pd.Index([])
	for df in frames:
		idx = idx.union(df.index)
	return list(idx.sort_values())


def run_backtest_multi(
	strategies: list[dict],
	data_map: dict[str, pd.DataFrame],
	commission: float,
	slippage: float,
	initial_cash: float = 1_000_000.0,
	allow_short: bool = True,
	price_field: str = "Close",
	initial_positions: Dict[str, int] | None = None,
	annual_mmf_rate: float = 0.0,
	lot_size: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
	
	pm = PortfolioManager(
		cash=initial_cash,
		commission=commission,
		slippage=slippage,
		allow_short=allow_short,
		initial_positions=initial_positions,
	)
	
	records = []
	fills_records: list[dict] = []
	dates = _union_sorted_indices(data_map.values())
	last_dt: pd.Timestamp | None = None
	# Baseline tracks
	bh_symbol = next(iter(data_map.keys())) if data_map else None
	bh_shares = None
	bh_cash = initial_cash
	mmf_only = initial_cash
	mmf_strategy_cashless = initial_cash  # not used; strategy uses pm
	flat_cash = initial_cash

	for dt in dates:
		if last_dt is not None:
			days = (dt - last_dt).days
			if days > 0 and annual_mmf_rate != 0:
				factor = (1 + annual_mmf_rate) ** (days / 365)
				pm.state.cash *= factor
				mmf_only *= factor
			else:
				factor = 1.0
		else:
			factor = 1.0
		last_dt = dt

		# prepare per-symbol latest price and history up to dt
		symbol_history: dict[str, pd.DataFrame] = {}
		price_map: dict[str, float] = {}
		for sym, df in data_map.items():
			hist = df.loc[:dt]
			if hist.empty:
				continue
			last_row = hist.iloc[-1]
			price = last_row.get(price_field)
			if price is None:
				continue
			symbol_history[sym] = hist
			price_map[sym] = float(price)

		# initialize buy&hold once we have first price for chosen symbol
		if bh_symbol and bh_symbol in price_map and bh_shares is None:
			px0 = price_map[bh_symbol]
			if px0 > 0:
				shares = int(initial_cash // (px0 * lot_size)) * lot_size
				bh_shares = shares
				bh_cash = initial_cash - shares * px0

		# gather orders per strategy
		for strat_cfg in strategies:
			obj = strat_cfg["obj"]
			name = strat_cfg.get("name", obj.__class__.__name__)
			target_symbols = strat_cfg.get("symbols", [])
			orders = {}
			for sym in target_symbols:
				hist = symbol_history.get(sym)
				if hist is None:
					continue
				try:
					dec = obj.decide(dt, hist)
				except Exception as e:
					logger.exception("Strategy decide failed: %s on %s", name, sym)
					continue
				for k, v in dec.items():
					orders[k] = orders.get(k, 0) + v

			if not orders:
				continue
			fills = pm.apply_orders(orders, price_map, strategy_name=name)
			for f in fills:
				fills_records.append({"date": dt, **f})

		# portfolio valuation
		position_value = sum(pm.state.positions.get(sym, 0) * price_map.get(sym, 0.0) for sym in pm.state.positions.keys())
		equity = pm.state.cash + position_value

		# baselines
		bh_equity = None
		if bh_shares is not None:
			bh_px = price_map.get(bh_symbol, None)
			if bh_px is not None:
				bh_equity = bh_shares * bh_px + bh_cash

		records.append((dt, equity, pm.state.cash, position_value, bh_equity, mmf_only, flat_cash))

	curve_df = pd.DataFrame(records, columns=['date', 'equity', 'cash', 'position_value', 'equity_buy_hold', 'equity_all_mmf', 'equity_flat']).set_index('date')
	curve_df['stock_return_pct'] = curve_df['position_value'].pct_change().fillna(0.0).replace([pd.NA, pd.NaT, float('inf'), float('-inf')], 0.0)
	# fill buy-hold forward if missing
	if 'equity_buy_hold' in curve_df.columns:
		curve_df['equity_buy_hold'] = curve_df['equity_buy_hold'].ffill()
	return curve_df, pd.DataFrame(fills_records)


# Backward-compat wrapper for single-strategy tasks
def run_backtest(strategy, data: pd.DataFrame, commission: float, slippage: float, initial_cash: float = 1_000_000.0):
	strategies = [{"obj": strategy, "symbols": [getattr(strategy, "symbol", None)], "name": strategy.__class__.__name__}]
	data_map = {getattr(strategy, "symbol", ""): data}
	return run_backtest_multi(
		strategies,
		data_map,
		commission,
		slippage,
		initial_cash,
		allow_short=True,
		price_field="Close",
		initial_positions=None,
		annual_mmf_rate=0.0,
		lot_size=1,
	)


__all__ = ["PortfolioManager", "run_backtest", "run_backtest_multi"]
