from __future__ import annotations

from typing import Optional

from src.factors.base import Factor


class Do_Nothing(Factor):
    """A factor that provides no opinion (always returns None)."""

    def calculate(self, context: "Context", symbol: str) -> Optional[float]:
        return None
