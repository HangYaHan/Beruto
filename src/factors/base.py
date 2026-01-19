from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict


class Factor(ABC):
    """
    Base class for all factors.
    """

    def __init__(self, params: Dict) -> None:
        """
        Initialize factor parameters.
        """
        self.params = params or {}

    @abstractmethod
    def calculate(self, context: "Context", symbol: str) -> Optional[float]:
        """
        Core calculation logic.

        Args:
            context: Full runtime context including account and market data.
            symbol: The symbol being evaluated.

        Returns:
            Target weight (0.0 ~ 1.0). None means no opinion.
        """
        raise NotImplementedError
