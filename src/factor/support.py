"""Factor helpers: triggers, on-bar hooks, and edge detectors.

This module centralizes tiny building blocks used by factors and the
backtest engine: per-instance `TriggerSet` to register actions without
global state collisions, backward-compatible global helpers
(`always`/`on_bar`/`run_triggers`), simple assertions/assignments, and
edge-detection utilities (`crossabove`/`crossbelow` plus PnL-based
`drawdown`/`take_profit`) that fire only on rising edges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Any
import pandas as pd

# Type aliases
Condition = Callable[[Any], bool]
Action = Callable[[Any], None]


@dataclass
class Trigger:
	condition: Condition
	action: Action
	name: Optional[str] = None
	last_state: bool = field(default=False, init=False)

	def evaluate(self, context: Any) -> None:
		"""Execute action on rising edge of condition (false -> true)."""
		current = False
		try:
			current = bool(self.condition(context))
		except Exception as exc:
			raise RuntimeError(f"Condition failed for trigger {self.name or ''}: {exc}") from exc

		if current and not self.last_state:
			try:
				self.action(context)
			except Exception as exc:
				raise RuntimeError(f"Action failed for trigger {self.name or ''}: {exc}") from exc
		self.last_state = current


class TriggerSet:
	"""Container to hold triggers and on-bar actions per factor instance."""

	def __init__(self) -> None:
		self._triggers: List[Trigger] = []
		self._on_bar: List[Action] = []

	def always(self, condition: Condition, action: Action, name: Optional[str] = None) -> Trigger:
		trig = Trigger(condition=condition, action=action, name=name)
		self._triggers.append(trig)
		return trig

	def on_bar(self, action: Action) -> Action:
		self._on_bar.append(action)
		return action

	def run(self, context: Any) -> None:
		for action in list(self._on_bar):
			action(context)
		for trig in list(self._triggers):
			trig.evaluate(context)


# Backward-compatible global trigger set (optional use)
_GLOBAL_SET = TriggerSet()


def always(condition: Condition, action: Action, name: Optional[str] = None) -> Trigger:
	return _GLOBAL_SET.always(condition, action, name)


def on_bar(action: Action) -> Action:
	return _GLOBAL_SET.on_bar(action)


def run_triggers(context: Any) -> None:
	_GLOBAL_SET.run(context)


def assign(value: Any) -> Any:
	return value


def assert_stmt(condition: bool, message: str = "assertion failed") -> None:
	if not condition:
		raise AssertionError(message)


def crossabove(a: pd.Series, b: pd.Series) -> pd.Series:
	"""Edge-trigger: a crosses above b (prev <=, now >)."""
	return (a > b) & (a.shift(1) <= b.shift(1))


def crossbelow(a: pd.Series, b: pd.Series) -> pd.Series:
	"""Edge-trigger: a crosses below b (prev >=, now <)."""
	return (a < b) & (a.shift(1) >= b.shift(1))


def drawdown(return_pct: pd.Series, threshold_pct: float, *, never: bool = False) -> pd.Series:
	"""Edge-trigger: return falls to or below -threshold_pct (pct as decimal).

	When `never` is True, returns an all-False series so the trigger never fires.
	"""
	series = pd.Series(return_pct, copy=False)
	if never:
		return pd.Series(False, index=series.index)
	if threshold_pct <= 0:
		raise ValueError("threshold_pct must be positive")
	threshold = abs(threshold_pct)
	breach = series <= -threshold
	prev_ok = series.shift(1) > -threshold
	return (breach & prev_ok).fillna(False)


def take_profit(return_pct: pd.Series, threshold_pct: float, *, never: bool = False) -> pd.Series:
	"""Edge-trigger: return reaches or exceeds threshold_pct (pct as decimal).

	When `never` is True, returns an all-False series so the trigger never fires.
	"""
	series = pd.Series(return_pct, copy=False)
	if never:
		return pd.Series(False, index=series.index)
	if threshold_pct <= 0:
		raise ValueError("threshold_pct must be positive")
	threshold = abs(threshold_pct)
	breach = series >= threshold
	prev_below = series.shift(1) < threshold
	return (breach & prev_below).fillna(False)


__all__ = [
	"Trigger",
	"TriggerSet",
	"always",
	"on_bar",
	"run_triggers",
	"assign",
	"assert_stmt",
	"crossabove",
	"crossbelow",
	"drawdown",
	"take_profit",
]
