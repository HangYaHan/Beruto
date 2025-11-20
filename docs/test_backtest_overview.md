# `tests/test_backtest.py` 概览

## 做了什么
- 构建 `MA20CrossoverStrategy`，在价格上穿 20 日均线时建仓、下穿时平仓，实现可重复的多空切换。
- 使用仓库自带的 `data/sh600000.parquet.csv`，统一收盘价列名并计算 20 日滚动均线。
- 逐日遍历数据：更新行情、生成/执行指令，并把当日资产、现金、持仓快照记录到 `vm.daily_snapshots`。
- 回测结束后打印 `VirtualManager.get_summary()`，再把价格、MA20、绝对 PnL 画到同一张图并输出为 `data/backtest_price_ma20_pnl.png`。

## 调用了哪些 `VirtualManager` 功能
- `add_strategy(...)`：把 `MA20CrossoverStrategy` 注册到投资组合管理器。
- `update_market_price(symbol, price)`：在每个交易日刷新单个标的的最新行情。
- `_aggregate_actions(date, history_slice)`：把所有策略在当前日期、给定历史数据窗口下的指令汇总成下单请求（脚本直接调了受保护方法）。
- `_execute_actions(actions, prices, timestamp)`：按当日价格撮合汇总指令，并写入交易历史 `vm.history`。
- `get_portfolio_value()`：在生成每日快照时获取最新组合净值。
- `get_summary()`：输出最终账户资金、仓位、收益等核心指标。
- 属性读写：
  - `vm.daily_snapshots`：手动追加每日净值/现金/持仓数据，供后续绘图。
  - `vm.history`：读取买卖记录，用于在图中标注买入/卖出点。

> 该脚本是一个可执行示例，而非 `pytest` 用例，主要用于验证 MA20 交叉策略和 `VirtualManager` 的联动流程及可视化输出。
