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

**3) 新增项目概览文档：`PROJECT_OVERVIEW.md`**
- 目的：在仓库根目录添加快速概览文件，描述各个顶层目录和主要模块的作用，便于开发者快速导航。
- 文件：`PROJECT_OVERVIEW.md`（位于仓库根）

---

**4) 新增调试脚本：`tests/_debug_fetch.py`**
- 目的：调试 `fetcher.get_history` 返回的数据结构（打印 columns 与前几行），用于定位列名不一致问题。
- 使用方法：
```powershell
Set-Location "E:\BETA STAR\FeedbackTrader"
python -u tests\_debug_fetch.py
```

---

**5) 修改：`tests/test_backtest.py`（归一化列名）**
- 目的：不同数据适配器返回的列名可能为小写（如 `close`），而脚本期望 `Close`。为兼容多适配器，在读取数据后做列名归一化处理。
- 修改位置：在读取 `df` 后、计算 `MA20` 之前增加列名映射：

```python
# 适配不同数据源返回的列名（有的适配器返回小写列名，如 'close'）
# 归一化为常用的首字母大写列名（Open/High/Low/Close/Adj Close/Volume）
col_map = {}
if 'close' in df.columns and 'Close' not in df.columns:
    col_map['close'] = 'Close'
if 'open' in df.columns and 'Open' not in df.columns:
    col_map['open'] = 'Open'
if 'high' in df.columns and 'High' not in df.columns:
    col_map['high'] = 'High'
if 'low' in df.columns and 'Low' not in df.columns:
    col_map['low'] = 'Low'
if 'volume' in df.columns and 'Volume' not in df.columns:
    col_map['volume'] = 'Volume'
if col_map:
    df = df.rename(columns=col_map)
```

影响：解决了 `KeyError: 'Close'` 的问题，使回测脚本能在 `akshare` 等适配器返回小写列名时正确运行。

---

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

**后续建议**
- 将 `VirtualManager._record_tx` 扩展为包含 `order_id`, `fee`, `slippage`, `strategy_id` 等字段，并在 `history` 中保留更标准化的时间格式（例如 ISO-8601 UTC 或 `pd.Timestamp`）。
- 若需要长期保存交易历史，考虑把 `history` 导出为 Parquet/CSV，或写入轻量数据库（SQLite）。
- 为 `VirtualManager` 增加更详细的日志（info/debug）以便回测过程中快速定位拒单/部分成交等原因。

如需我把这些变更提交为 git commit（并推送），或进一步扩展 `_record_tx` 的字段与测试，请告诉我下一步操作。
