# Beruto

Beruto 是一个基于 Rust 的股票回测 CLI 工具，当前重点是：
- 统一的 `run` 入口
- 单一系统配置文件
- manager / portfolio 语义分层
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
- 单标的策略回测与批量任务执行。
- 已开始支持手续费、交易税、过户费、现金分红与红利税拆分。
- 结果包含：
  - `initial_capital`
  - `final_equity`
  - `gross_final_equity`
  - `total_return_pct`
  - `gross_return_pct`
  - `net_return_pct`
  - `max_drawdown_pct`
  - `trades`
  - `commission_total`
  - `transaction_tax_total`
  - `transfer_fee_total`
  - `dividend_income_total`
  - `dividend_tax_total`
  - `tax_fee_total`
  - `equity_curve`

### 4) CLI
- 交互式 REPL。
- 命令覆盖：帮助、清屏、拉取数据、策略查看、配置管理、`run`、排行榜、可视化、清理结果。
- `backtest` 已移除，统一由 `run` 承担执行入口。

### 5) 存储
- 单次回测结果：`target/debug/result/run_*.json`（或对应可执行文件目录下的 `result/`）
- 批量任务摘要：`target/debug/result/batch_*.json`

## 快速开始

### 1) 启动
```bash
cargo run
```

### 2) 常用流程
```text
beruto> fetch 600519
beruto> config show
beruto> run --plan plans/minimal_void_plan.json --force
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
- 统一方案与阶段规划：`docs/UNIFIED_PORTFOLIO_TAX_BACKTEST_PLAN.md`
- manager 样例与测试说明：`managers/README.md`

## 设计约定
- `run` 是唯一执行入口，plan 负责描述 manager、symbol 与参数。
- `portfolio` 是运行时状态，`manager` 是决策策略。
- 先保证“可运行 + 可追溯”，再逐步演进更复杂的事件循环与学习型 manager。