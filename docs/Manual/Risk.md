# risk

来源：`src/risk/risk_manager.py`

## 类
- `class RiskManager`：
  - `__init__(self, max_position: float | None = None, max_drawdown: float | None = None)`：初始化风险阈值（当前未使用）。
  - `check_order(self, portfolio: Any, order: dict) -> bool`：占位函数，用于按风险规则校验订单。
  - `calculate_exposure(self, portfolio: Any) -> float`：占位函数，用于计算敞口指标。

风控逻辑尚未实现；可扩展 `check_order` 与 `calculate_exposure` 以落地仓位限制、回撤控制等规则。
