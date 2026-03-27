# Beruto

## 项目目标
构建一个基于 Rust 的股票回测与仓位管理系统，围绕标的 159581 进行策略研究。长期目标是形成可扩展的框架，逐步加入 GUI、更多策略与量化接口。

## 开发原则
- 从最小可运行版本开始。
- 每次只做一小步，并保持可编译、可运行。
- 先完成 CLI 回测闭环，再扩展复杂功能。

## 当前实现摘要（2026-03-21）

更新（2026-03-27）：CLI 已支持 `backtest/bt` 二级回测子系统，新增逐项参数输入流程与可持久化 settings。

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
- 已实现交互式回测子系统：
	- 输入 `bt` 进入 `bt>` 子提示符。
	- 支持逐项提示输入策略参数（回车可采用默认）。
	- 支持直接输入策略名进入参数向导（如 `bt> macd`）。
- 已实现 settings 配置持久化：
	- 全局默认值（symbol、initial-capital）。
	- 各策略参数默认值（包括 MACD/KDJ/Contrarian）。
	- 保存路径 `.beruto/settings.json`。
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

### 推荐交互路径
1. 运行 `cargo run`。
2. 在 `beruto>` 输入 `bt`。
3. 在 `bt>` 输入 `run`（或直接输入策略名）按提示逐项输入参数。
4. 使用 `settings` 管理默认参数并自动持久化。

## 接下来做什么
后续按 step-by-step 计划推进，详见 `TODO.md`。