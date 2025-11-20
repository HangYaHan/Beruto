**Manager Record Change**

- **Date**: 2025-11-19
- **Author**: 自动更新（由开发助理在工作区修改）
- **File**: `src/portfolio/manager.py`

**变更摘要**:
- 在 `VirtualManager` 类中新增 `_record_tx` 方法，用以记录每次成交（BUY/SELL）到 `self.history`。

**为什么需要该变更**:
- 原实现的 `_buy_at` 与 `_sell_at` 在成交后调用 `self._record_tx(...)`，但并未实现该方法，导致第一次成交时抛出 `AttributeError`。
- 为了修复此异常并能保存逐笔交易记录，添加了 `_record_tx` 的实现。

**实现细节**:
- 方法签名：`def _record_tx(self, side: str, symbol: str, quantity: int, price: float, timestamp: Optional[datetime] = None) -> None`。
- 存储位置：`self.history`（列表），追加的每条记录为字典，包含字段：
  - `type`: 成交类型，`BUY` / `SELL`
  - `symbol`: 标的代码
  - `quantity`: 成交数量（int）
  - `price`: 成交价（float）
  - `timestamp`: 如果传入则使用 `timestamp.isoformat()`，否则为 `str(timestamp)`（可能为 `None` 的字符串）
  - `cash`: 成交后 `self.cash`（float）
  - `positions`: 成交后持仓快照（对 `self.positions` 做 `deepcopy`）

**测试**:
- 新增单元测试文件 `tests/test_portfolio_manager.py`，覆盖买入、卖出、资金不足按比例买入、以及 `get_summary`/`history` 行为。
- 在本地运行 `pytest tests/test_portfolio_manager.py`，测试通过：`3 passed`。

**兼容性与注意事项**:
- 当前 `_record_tx` 使用 `deepcopy(self.positions)` 记录持仓快照，方便回测分析，但在高频或包含大量持仓时可能有性能或内存开销。后续可改为记录增量或仅记录变更字段。
- `timestamp` 以字符串形式保存（ISO 格式或 `str(None)`），若需要更严格的时间处理，建议改为保存 `pd.Timestamp` 或 UTC ISO 字符串并保证统一时区。

**后续建议**:
- 考虑加入更多字段：手续费 (`fee`)、滑点 (`slippage`)、事件 ID、订单 id、成交来源（策略 id）等，以便更精确回测与审计。
- 将交易记录持久化到文件（CSV/Parquet）或数据库，以便长期分析和避免内存溢出。
- 若需要高性能回测，可以将 `history` 改为按天汇总的轻量结构，或延后 deep-copy 至最终输出阶段。


