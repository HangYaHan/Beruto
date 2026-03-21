# Beruto

## 项目目标
构建一个基于 Rust 的股票回测与仓位管理系统，围绕标的 159581 进行策略研究。长期目标是形成可扩展的框架，逐步加入 GUI、更多策略与量化接口。

## 开发原则
- 从最小可运行版本开始。
- 每次只做一小步，并保持可编译、可运行。
- 先完成 CLI 回测闭环，再扩展复杂功能。

## 当前实现摘要（2026-03-21）

### 1) 已完成的最小回测闭环
- 可从本地 CSV 读取 159581 日线数据：`data/159581_daily.csv`。
- 已实现策略接口 `Strategy` 与信号 `Signal`（Buy/Hold/Sell）。
- 已实现两种策略：
	- BuyAndHold（首次买入后长期持有）。
	- ContrarianSimple（可配置涨跌阈值的逆向策略）。
- 已实现回测引擎：
	- 支持全仓买入/清仓卖出。
	- 生成净值曲线。
	- 计算总收益率、最大回撤、交易次数。
- `main` 中可直接运行并打印：
	- 数据基本信息。
	- BuyAndHold 与 Contrarian 的回测摘要。
	- Contrarian 多组阈值 sweep 对比结果。

### 2) 测试现状
- 已有集成测试（`tests/integration_tests.rs`）：
	- CSV 可加载。
	- 回测结果字段基本有效。
	- Contrarian 默认阈值与可配置阈值都可运行。

### 3) 当前目录状态
- 已有模块骨架：
	- `src/data`
	- `src/strategy`
	- `src/backtest`
	- `src/gui`
	- `tests`
- 其中 GUI 相关文件与 `src/data/storage.rs` 目前仍为空，属于后续阶段任务。

## 运行方式
- 运行主程序：`cargo run`
- 运行测试：`cargo test`

## 接下来做什么
后续按 step-by-step 计划推进，详见 `TODO.md`。