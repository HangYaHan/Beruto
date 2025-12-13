# portfolio

来源：`src/portfolio/manager.py`

## 类
- `class PortfolioState`：轻量级结构体，保存 `cash: float`、`positions: dict[str, int]`、`history: list[dict]`。
  - `equity(prices: dict[str, float]) -> float`：用当前价格将仓位市值化，与现金相加得到总权益。

- `class PortfolioManager`：
  - `__init__(self, initial_cash: float = 1_000_000, commission: float = 0.0, slippage: float = 0.0)`：初始化资金与交易成本。
  - `snapshot(self, prices: dict[str, float]) -> dict`：生成当前账户快照（含权益和持仓）。
  - `apply_orders(self, orders: dict[str, int], prices: dict[str, float]) -> None`：执行市价单，计入手续费与滑点后更新现金和持仓。
  - `value(self, prices: dict[str, float]) -> float`：便捷计算当前权益。

## 函数
- `run_backtest(strategy, data: pandas.DataFrame, commission: float = 0.0, slippage: float = 0.0, initial_cash: float = 1_000_000) -> pandas.DataFrame`：按历史数据逐日回放，每根 K 线调用 `strategy.decide(date, history)` 获取订单，通过 `PortfolioManager` 执行，返回按日期索引的权益曲线。
