"""
Portfolio manager interface:
- manage positions, cash, valuation
- provide order suggestions and fill callbacks
"""
from typing import Dict, Any

class VirtualManager:
    name: str
    





class Portfolio:
    def __init__(self, initial_cash: float, config: Dict[str, Any]):
        """Initialize the portfolio."""
        pass

    def allocate(self, symbol: str, quantity: float) -> None:
        """Adjust position allocation (modify internal target position)."""
        pass

    def update_on_fill(self, order: Dict[str, Any], fill: Dict[str, Any]) -> None:
        """Callback when an order is filled; update positions and cash."""
        pass

    def get_positions(self) -> Dict[str, Any]:
        """Return a snapshot of current positions."""
        pass

    def get_value(self) -> float:
        """Return the current portfolio value (including cash)."""
        pass