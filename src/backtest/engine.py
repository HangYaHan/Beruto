"""Backtest engine that loads task JSON and runs the specified strategy."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.data import fetcher
from src.portfolio.manager import run_backtest
from src.system.log import get_logger

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
	equity_curve = run_backtest(strategy, df, commission=commission, slippage=slippage, initial_cash=initial_cash)
	logger.info("Backtest finished: start=%s end=%s final_equity=%.2f", df.index.min(), df.index.max(), equity_curve.iloc[-1,0])
	return equity_curve


__all__ = ["run_task"]
