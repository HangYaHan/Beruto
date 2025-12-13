# execution

来源：`src/execution/broker.py`

## 接口
- `class BrokerInterface`：抽象券商接口。
  - `place_order(symbol: str, qty: int, price: float | None = None, order_type: str = 'market') -> str`：下单并返回券商订单 id。
  - `cancel_order(order_id: str) -> bool`：按 id 撤单，返回是否成功。
  - `get_order_status(order_id: str) -> dict`：返回指定订单的状态信息。

当前未提供实现；如需对接真实券商，请继承 `BrokerInterface` 并实现上述三个方法。
