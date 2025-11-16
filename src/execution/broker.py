"""
Broker / Execution interface definitions.
- place_order / cancel_order / get_order_status / simulate_fill, etc.
- Live (production) adapters should implement these interfaces.
"""
from typing import Dict, Any


class BrokerInterface:
    def place_order(self, order: Dict[str, Any]) -> str:
        """Place an order, return order_id (string)."""
        raise NotImplementedError

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order, return whether it succeeded."""
        raise NotImplementedError

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Query an order status, return a dict describing it."""
        raise NotImplementedError