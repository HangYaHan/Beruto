"""Preview-oriented strategy runner aligned to the new factor plan format.

This module now focuses on loading and validating strategy plans (factor wiring)
without bundling start/end dates or execution settings. A future backtest engine
can consume the same plan objects.
"""

from __future__ import annotations

from typing import Dict, Any

from src.strategy import StrategyPlan, load_plan
from src.system.log import get_logger

logger = get_logger(__name__)


def summarize_plan(plan: StrategyPlan) -> Dict[str, Any]:
	"""Return a lightweight summary for UI/CLI usage."""
	return {
		"name": plan.name,
		"description": plan.description or "",
		"symbols": list(plan.symbols),
		"factors": [
			{
				"name": f.name,
				"module": f.module,
				"class": f.class_name,
				"symbols": list(f.symbols),
				"params": dict(f.params),
			}
			for f in plan.factors
		],
	}


def run_task(plan_name: str) -> StrategyPlan:
	"""Load a strategy plan by name and return it.

	The previous "task" idea mapped to backtests with calendar/execution settings.
	After the redesign, a task is simply a plan alias that defines which factors
	apply to which symbols. Downstream engines can decide how to execute it.
	"""
	plan = load_plan(plan_name)
	logger.info("Loaded plan %s with %s factors targeting %s symbols", plan.name, len(plan.factors), len(plan.symbols))
	return plan


__all__ = ["run_task", "summarize_plan"]
