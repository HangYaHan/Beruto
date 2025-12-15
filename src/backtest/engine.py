"""Backtest engine that loads task JSON and runs the specified strategy."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.data import fetcher
from src.portfolio.manager import run_backtest_multi
from src.system.startup import new_result_run_dir
from src.system.log import get_logger
import matplotlib.pyplot as plt

logger = get_logger(__name__)


def load_task(task_name: str) -> Dict[str, Any]:
	task_path = Path(__file__).resolve().parents[2] / 'tasks' / f'{task_name}.json'
	if not task_path.exists():
		raise FileNotFoundError(f"Task file not found: {task_path}")
	with task_path.open('r', encoding='utf-8') as f:
		return json.load(f)


def load_strategy(module_path: str, class_name: str, params: Dict[str, Any]):
	module = importlib.import_module(module_path)
	cls = getattr(module, class_name)
	return cls(**params)


def run_task(task_name: str):
	task = load_task(task_name)
	logger.info("Loaded task %s", task_name)

	universe = task.get('universe', {})
	strategies_cfg = task.get('strategies', [])
	portfolio_cfg = task.get('portfolio', {})
	exec_cfg = task.get('execution', {})
	calendar_cfg = task.get('calendar', {})
	outputs_cfg = task.get('outputs', {})

	data_cfg = universe.get('data', {})
	symbols = universe.get('symbols', [])
	if not symbols:
		raise ValueError("No symbols defined in universe.symbols")

	strategies = []
	for scfg in strategies_cfg:
		obj = load_strategy(scfg['module'], scfg['class'], scfg.get('params', {}))
		on_syms = scfg.get('routing', {}).get('on', scfg.get('params', {}).get('symbol', []))
		if isinstance(on_syms, str):
			on_syms = [on_syms]
		strategies.append({"name": scfg.get('name', obj.__class__.__name__), "obj": obj, "symbols": on_syms})
		logger.info("Strategy instantiated: %s.%s name=%s params=%s routes=%s", scfg['module'], scfg['class'], scfg.get('name'), scfg.get('params'), on_syms)

	start_date = calendar_cfg.get('start') or data_cfg.get('start')
	end_date = calendar_cfg.get('end') or data_cfg.get('end')
	price_field = exec_cfg.get('price_field', 'Close')

	data_map = {}
	for sym in symbols:
		df = fetcher.get_history(
			symbol=sym,
			start=start_date,
			end=end_date,
			source=data_cfg.get('source', 'akshare'),
			interval=data_cfg.get('interval', '1d'),
			cache=data_cfg.get('cache', True),
			refresh=data_cfg.get('refresh', False),
		)
		if price_field not in df.columns:
			if price_field.lower() in df.columns:
				df = df.rename(columns={price_field.lower(): price_field})
			elif 'close' in df.columns:
				df = df.rename(columns={'close': price_field})
			else:
				raise ValueError(f"Data for {sym} missing price field {price_field}")
		logger.info("Data fetched: symbol=%s rows=%s start=%s end=%s", sym, len(df), df.index.min(), df.index.max())
		data_map[sym] = df

	commission = portfolio_cfg.get('commission', 0.0)
	slippage = portfolio_cfg.get('slippage', 0.0)
	initial_cash = portfolio_cfg.get('cash', 1_000_000.0)
	allow_short = portfolio_cfg.get('allow_short', True)
	initial_positions = portfolio_cfg.get('initial_positions', {})

	logger.info("Running backtest: cash=%.2f commission=%.4f slippage=%.4f allow_short=%s", initial_cash, commission, slippage, allow_short)
	run_dir = new_result_run_dir()
	annual_mmf_rate = exec_cfg.get('annual_mmf_rate', 0.02)
	lot_size = exec_cfg.get('lot_size', 1)
	curve, trades = run_backtest_multi(
		strategies,
		data_map,
		commission=commission,
		slippage=slippage,
		initial_cash=initial_cash,
		allow_short=allow_short,
		price_field=price_field,
		initial_positions=initial_positions,
		annual_mmf_rate=annual_mmf_rate,
		lot_size=lot_size,
	)
	final = curve.iloc[-1]
	logger.info(
		"Backtest finished: start=%s end=%s final_equity=%.2f cash=%.2f position_value=%.2f stock_return=%.4f",
		min(df.index.min() for df in data_map.values()),
		max(df.index.max() for df in data_map.values()),
		final['equity'], final['cash'], final['position_value'], final['stock_return_pct']
	)
	# Persist equity curve
	curve_path = run_dir / "equity_curve.csv"
	curve.to_csv(curve_path)
	logger.info("Saved equity curve to %s", curve_path)

	# Plot equity/cash/position_value curves
	try:
		fig, ax = plt.subplots(figsize=(10, 5))
		curve[['equity', 'cash', 'position_value']].plot(ax=ax)
		sym_title = ",".join(symbols)
		ax.set_title(f"Equity/Cash/Position for {sym_title}")
		ax.set_ylabel("Value")
		ax.grid(True, alpha=0.3)
		ax.legend()
		plot_path = run_dir / "equity_plot.png"
		fig.savefig(plot_path, dpi=120, bbox_inches='tight')
		plt.close(fig)
		logger.info("Saved equity plot to %s", plot_path)
	except Exception as e:
		logger.exception("Failed to save equity plot: %s", e)

	# Plot baseline curves on one chart
	try:
		cols = [c for c in ['equity', 'equity_buy_hold', 'equity_all_mmf', 'equity_flat'] if c in curve.columns]
		if cols:
			fig, ax = plt.subplots(figsize=(10, 5))
			curve[cols].plot(ax=ax)
			ax.set_title("Equity Baselines vs Strategy")
			ax.set_ylabel("Value")
			ax.grid(True, alpha=0.3)
			ax.legend()
			plot_path = run_dir / "equity_baselines.png"
			fig.savefig(plot_path, dpi=120, bbox_inches='tight')
			plt.close(fig)
			logger.info("Saved equity baseline plot to %s", plot_path)
	except Exception as e:
		logger.exception("Failed to save equity baseline plot: %s", e)

	# Persist trades log (txt only, date only)
	if trades is not None and not trades.empty:
		trades_txt = run_dir / "trades.txt"
		with trades_txt.open('w', encoding='utf-8') as f:
			for _, r in trades.iterrows():
				date_str = pd.to_datetime(r['date']).date()
				f.write(f"{date_str}: {r['side']} {r['symbol']} qty={r['qty']} price={r['price']:.4f} fee={r['fee']:.2f}\n")
		logger.info("Saved trades to %s", trades_txt)

	# Append leaderboard
	leaderboard_path = run_dir.parent / "leaderboard.csv"
	sym_title = ",".join(symbols)
	row = {
		"symbol": sym_title,
		"start": str(min(df.index.min() for df in data_map.values())),
		"end": str(max(df.index.max() for df in data_map.values())),
		"strategy_module": ",".join(s.get('module', '') for s in strategies_cfg),
		"strategy_class": ",".join(s.get('class', '') for s in strategies_cfg),
		"strategy_params": json.dumps([s.get('params', {}) for s in strategies_cfg], ensure_ascii=False),
		"initial_cash": initial_cash,
		"final_equity": float(final['equity']),
		"return_pct": (float(final['equity']) / float(initial_cash)) - 1.0,
	}
	import csv
	header = list(row.keys())
	write_header = not leaderboard_path.exists()
	with leaderboard_path.open('a', newline='', encoding='utf-8') as f:
		w = csv.DictWriter(f, fieldnames=header)
		if write_header:
			w.writeheader()
		w.writerow(row)
	logger.info("Appended leaderboard row to %s", leaderboard_path)

	return curve


__all__ = ["run_task"]
