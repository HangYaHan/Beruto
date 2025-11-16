"""
Risk management module interfaces.
- check_order: evaluate order compliance before placing
- calculate_exposure: compute portfolio/account risk metrics
"""
from typing import Dict, Any


class RiskManager:
    def __init__(self, config: Dict[str, Any]):
        pass

    def check_order(self, order: Dict[str, Any], portfolio: Any) -> bool:
        """
        Validate an order before placement (funds, position limits, per-order checks, etc.).
        Return True to allow the order, False to reject.
        """
        pass

    def calculate_exposure(self, portfolio: Any) -> Dict[str, Any]:
        """Compute and return current risk exposure (e.g., leverage, concentration)."""
        pass