from __future__ import annotations

from typing import Dict, Optional

from src.factors.base import Factor


class Buy_Hold(Factor):
	"""Buy on day 1 using x fraction of initial cash, then hold."""

	def __init__(self, params: Dict) -> None:
		super().__init__(params)
		self.x = float(params.get("x", 1.0))
		self._weights: Optional[Dict[str, float]] = None

	def _compute_weights(self, context: "Context") -> None:
		universe = getattr(context.data_proxy, "_universe", []) or []
		if not universe:
			self._weights = {}
			return
		x_clamped = max(0.0, min(1.0, self.x))
		per_symbol = x_clamped / len(universe)
		self._weights = {code: per_symbol for code in universe}

	def calculate(self, context: "Context", symbol: str) -> Optional[float]:
		if self._weights is None:
			self._compute_weights(context)
		return self._weights.get(symbol) if self._weights else None


__all__ = ["Buy_Hold"]
