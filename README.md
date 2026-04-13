# Beruto

Beruto 是一个基于 Rust 的股票回测 CLI 工具，当前重点是：
- 单次回测（`backtest`）
- 批量任务（`run`，会先展开成多个 backtest 任务执行）
- 结果持久化（JSON）

## 当前能力

### 1) 数据
- 支持按股票代码加载日线数据（CSV）。
- 若本地缺失数据，可通过 EastMoney 接口拉取并写入 `data/<symbol>_daily.csv`。

### 2) 策略
- `buyhold`：首次信号买入后持有。
- `contrarian`：按阈值做逆向交易（下跌买入、上涨卖出）。
- `kdj`：使用 KDJ 随机指标，在 J 线进入超卖/超买区间时交易。

### 3) 回测引擎
- 全仓买入/清仓卖出。
- 结果包含：
  - `initial_capital`
  - `final_equity`
  - `total_return_pct`
  - `max_drawdown_pct`
  - `trades`
  - `equity_curve`

### 4) CLI
- 交互式 REPL。
- 命令覆盖：帮助、清屏、拉取数据、策略查看、单次回测、批量回测、排行榜、清理结果。

### 5) 存储
- 单次回测结果：`.beruto/results/run_*.json`
- 批量任务摘要：`.beruto/results/batch_*.json`

## 快速开始

### 1) 启动
```bash
cargo run
```

### 2) 常用流程
```text
beruto> fetch 600519
beruto> backtest --symbol 600519 --strategy buyhold
beruto> backtest --symbol 600519 --strategy kdj --kdj-period 9 --kdj-buy-threshold 20 --kdj-sell-threshold 80
beruto> run --symbols 159581,600519 --strategies buyhold,contrarian --buy-drop-values -1.0,-0.8 --sell-rise-values 1.0,1.2
beruto> leaderboard --top 10
```

### 3) 测试
```bash
cargo test
```

## 文档索引
- 命令和参数说明 + 示例：`EXAMPLE.md`
- `src` 目录文件职责说明：`SRC_OVERVIEW.md`

## 设计约定
- `run` 的所有执行都会先展开为 backtest 任务，再复用现有回测模块逐个执行。
- 先保证“可运行 + 可追溯”，再逐步演进数据库与更复杂调度能力。