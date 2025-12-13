"""Backtest engine that loads task JSON and runs the specified strategy."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.data import fetcher
from src.portfolio.manager import run_backtest
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

	strat_cfg = task['strategy']
	port_cfg = task['portfolio']
	data_cfg = task['data']

	strategy = load_strategy(strat_cfg['module'], strat_cfg['class'], strat_cfg['params'])
	logger.info("Strategy instantiated: %s.%s params=%s", strat_cfg['module'], strat_cfg['class'], strat_cfg['params'])

	df = fetcher.get_history(
		symbol=data_cfg['symbol'],
		start=data_cfg.get('start', port_cfg.get('start')),
		end=data_cfg.get('end', port_cfg.get('end')),
		source=data_cfg.get('source', 'akshare'),
		interval=data_cfg.get('interval', '1d'),
		cache=data_cfg.get('cache', True),
		refresh=data_cfg.get('refresh', False),
	)
	logger.info("Data fetched: symbol=%s rows=%s start=%s end=%s", data_cfg['symbol'], len(df), df.index.min(), df.index.max())

	# ensure Close exists
	if 'Close' not in df.columns:
		# try to infer from common names
		if 'close' in df.columns:
			df = df.rename(columns={'close': 'Close'})
		else:
			raise ValueError('DataFrame must contain Close column')

	commission = port_cfg.get('commission', 0.0)
	slippage = port_cfg.get('slippage', 0.0)
	initial_cash = port_cfg.get('cash', 1_000_000.0)

	logger.info("Running backtest: cash=%.2f commission=%.4f slippage=%.4f", initial_cash, commission, slippage)
	# Prepare result directory
	run_dir = new_result_run_dir()
	curve, trades = run_backtest(strategy, df, commission=commission, slippage=slippage, initial_cash=initial_cash)
	final = curve.iloc[-1]
	logger.info(
		"Backtest finished: start=%s end=%s final_equity=%.2f cash=%.2f position_value=%.2f stock_return=%.4f",
		df.index.min(), df.index.max(), final['equity'], final['cash'], final['position_value'], final['stock_return_pct']
	)
	# Persist equity curve
	curve_path = run_dir / "equity_curve.csv"
	curve.to_csv(curve_path)
	logger.info("Saved equity curve to %s", curve_path)

	# Plot equity/cash/position_value curves
	try:
		fig, ax = plt.subplots(figsize=(10, 5))
		curve[['equity', 'cash', 'position_value']].plot(ax=ax)
		ax.set_title(f"Equity/Cash/Position for {data_cfg['symbol']}")
		ax.set_ylabel("Value")
		ax.grid(True, alpha=0.3)
		ax.legend()
		plot_path = run_dir / "equity_plot.png"
		fig.savefig(plot_path, dpi=120, bbox_inches='tight')
		plt.close(fig)
		logger.info("Saved equity plot to %s", plot_path)
	except Exception as e:
		logger.exception("Failed to save equity plot: %s", e)

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
	row = {
		"symbol": data_cfg['symbol'],
		"start": str(df.index.min()),
		"end": str(df.index.max()),
		"strategy_module": strat_cfg['module'],
		"strategy_class": strat_cfg['class'],
		"strategy_params": json.dumps(strat_cfg.get('params', {}), ensure_ascii=False),
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
