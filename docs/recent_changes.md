**Recent Changes Summary**

- **Date**: 2025-11-20
- **Author**: Assistant (code edits made in working tree)

下面记录我最近在仓库中所做的修改、添加的文件，以及关键代码片段。文档同时包含如何在本地运行测试/回测来验证这些更改。

---

**1) 新增并修复：`src/portfolio/manager.py`**
- 目的：修复 `VirtualManager` 在执行成交时调用 `_record_tx` 但未实现造成的 AttributeError，并添加逐笔交易记录功能。
- 文件：`src/portfolio/manager.py`
- 关键新增代码片段（完整实现见文件）：

```python
    def _record_tx(self, side: str, symbol: str, quantity: int, price: float, timestamp: Optional[datetime] = None) -> None:
        """
        记录逐笔交易到 `self.history`。保留成交类型、标的、数量、价格、时间、成交后现金和持仓快照。
        """
        tx = {
            "type": side,
            "symbol": symbol,
            "quantity": int(quantity),
            "price": float(price),
            "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
            "cash": float(self.cash),
            "positions": copy.deepcopy(self.positions),
        }
        self.history.append(tx)
```

**影响/说明**:
- _record_tx 会将每次成交后的持仓快照做 deepcopy 并追加到 `self.history`，方便后续审计和结果分析。
- 注意：deepcopy 在大规模持仓或高频场景会带来内存/性能开销，后续可考虑按需优化。

---

**2) 新增单元测试：`tests/test_portfolio_manager.py`**
- 目的：为 `VirtualManager` 增加单元测试，覆盖买入、卖出、资金不足时部分买入、summary/history 行为。
- 文件：`tests/test_portfolio_manager.py`
- 测试概览：
  - `test_buy_and_hold_and_sell_flow`：检验买入、更新市价、卖出产生的 realized/unrealized pnl 与现金变动。
  - `test_insufficient_cash_buys_partial`：检验资金不足时按价格向下取整买入行为。
  - `test_summary_and_history_records`：检验 `get_summary()` 与 `history` 记录存在。

测试状态：在本地环境使用 `pytest` 运行该测试文件结果为 `3 passed`。

---



---


**3) 修改：`tests/test_backtest.py`（归一化列名）**
- 构建 `MA20CrossoverStrategy`，在价格上穿 20 日均线时建仓、下穿时平仓，实现可重复的多空切换。
- 使用仓库自带的 `data/sh600000.parquet.csv`，统一收盘价列名并计算 20 日滚动均线。
- 逐日遍历数据：更新行情、生成/执行指令，并把当日资产、现金、持仓快照记录到 `vm.daily_snapshots`。
- 回测结束后打印 `VirtualManager.get_summary()`，再把价格、MA20、绝对 PnL 画到同一张图并输出为 `data/backtest_price_ma20_pnl.png`。

#### 调用了哪些 `VirtualManager` 功能
- `add_strategy(...)`：把 `MA20CrossoverStrategy` 注册到投资组合管理器。
- `update_market_price(symbol, price)`：在每个交易日刷新单个标的的最新行情。
- `_aggregate_actions(date, history_slice)`：把所有策略在当前日期、给定历史数据窗口下的指令汇总成下单请求（脚本直接调了受保护方法）。
- `_execute_actions(actions, prices, timestamp)`：按当日价格撮合汇总指令，并写入交易历史 `vm.history`。
- `get_portfolio_value()`：在生成每日快照时获取最新组合净值。
- `get_summary()`：输出最终账户资金、仓位、收益等核心指标。
- 属性读写：
  - `vm.daily_snapshots`：手动追加每日净值/现金/持仓数据，供后续绘图。
  - `vm.history`：读取买卖记录，用于在图中标注买入/卖出点。


**如何在本地复现/验证**
1. 进入项目根目录并激活虚拟环境（Windows PowerShell）：
```powershell
Set-Location "E:\BETA STAR\FeedbackTrader"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest
```
2. 运行单元测试：
```powershell
pytest -q tests/test_portfolio_manager.py
```
3. 运行回测脚本（示例）：
```powershell
python tests\test_backtest.py
```

---


