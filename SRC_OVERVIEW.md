# SRC_OVERVIEW

本文档记录当前 `src` 目录每个 Rust 文件的职责（基于当前代码状态）。

## 根模块

- `src/main.rs`
  - 可执行入口。
  - 启动 CLI REPL（`cli::run_repl`），发生错误时打印并退出。

- `src/lib.rs`
  - 库入口。
  - 导出 `backtest`、`data`、`strategy`、`portfolio`、`manager` 模块。

## CLI 模块

- `src/cli/mod.rs`
  - CLI 主入口与聚合文件。
  - 保留 REPL 循环与公共 `use`，通过 `include!` 组合子文件实现。

- `src/cli/core_commands.rs`
  - 基础命令分发与轻量命令实现。
  - 包含 `execute_line`、`strategy`、`config`、`run` 分发、清屏以及 config 值解析与路径写入逻辑。

- `src/cli/run_planning.rs`
  - 批量回测计划与通用工具。
  - 包含 run plan 读取、run 参数合并、日期校验、日期过滤、数值参数提取等函数。

- `src/cli/backtest_flow.rs`
  - 回测主流程与批量执行。
  - 包含任务展开、任务去重 key、单次/批量回测执行、结果保存、排行榜与回测结果打印。

- `src/cli/backtest_reporting.rs`
  - 回测结果展示相关函数。
  - 包含单次结果打印与 `leaderboard` 命令实现。

- `src/cli/visualization_and_clean.rs`
  - 可视化与清理命令实现。
  - 包含单次/批量可视化 HTML 输出、批次记录聚合、`clean` 命令。

- `src/cli/help.rs`
  - CLI 展示函数。
  - 负责打印 banner 与 help 命令列表。

- `src/cli/parser.rs`
  - CLI 参数解析工具。
  - 提供 flag 读取、数值解析、逗号列表解析。

## 回测模块

- `src/backtest/mod.rs`
  - 回测模块导出文件。
  - 声明 `engine`、`result` 子模块。

- `src/backtest/engine.rs`
  - 回测执行引擎。
  - 按策略信号驱动仓位变化并生成净值曲线。
  - 计算毛收益、净收益、分红、手续费与税费拆分。

- `src/backtest/result.rs`
  - 回测结果数据结构定义 `BacktestResult`。
  - 可序列化，用于持久化与展示。

## 数据模块

- `src/data/mod.rs`
  - 数据模块导出文件。
  - 声明 `data_source`、`fetcher`、`storage` 子模块。

- `src/data/data_source.rs`
  - 数据读取与解析。
  - 加载本地 CSV 为 `DailyQuote` 列表。
  - 支持可选分红列 `dividend_per_share`（缺列时回退为 0）。
  - 若指定 symbol 对应文件不存在，会触发在线拉取。

- `src/data/fetcher.rs`
  - 在线数据拉取实现。
  - 调用 EastMoney 接口获取日线数据并写入 CSV。
  - 生成 `dividend_per_share` 列（当前默认写入 0.0，为后续分红数据源预留）。
  - 包含代码规范化、市场前缀映射、基本校验。

- `src/data/storage.rs`
  - 回测结果存储与加载。
  - 管理可执行文件旁的 `result` 目录。
  - 保存单次 run 记录、加载历史记录、清理结果文件。

## 策略模块

- `src/strategy/mod.rs`
  - 策略注册与构建中心。
  - 定义策略元信息（`StrategySpec`）与运行配置（`StrategyConfig`）。
  - 根据配置构造具体策略实例。

## 组合与管理器模块

- `src/portfolio/mod.rs`
  - 组合账户与持仓基础模型。
  - 定义 `Portfolio`、`Position`、`PortfolioConfig` 与基础权益/敞口计算。

- `src/manager/mod.rs`
  - 管理器抽象与基础实现。
  - 定义 `Manager` trait、`SignalIntent`、`ManagerContext`、`OrderDecision`、`ManagerKind`。
  - 提供 `VoidManager` 与 `ScoreRankManager` 作为当前首版骨架。

- `src/strategy/base.rs`
  - 策略抽象层。
  - 定义 `Signal` 枚举和 `Strategy` trait。

- `src/strategy/buy_and_hold.rs`
  - 策略实现。
  - 买入并持有策略。

- `src/strategy/contrarian.rs`
  - 策略实现。
  - 包含 `ContrarianStrategy`。
  - `ContrarianStrategy` 支持阈值配置。

- `src/strategy/kdj.rs`
  - 策略实现。
  - 基于 KDJ 指标的策略。

- `src/strategy/macd.rs`
  - 策略实现。
  - 基于 MACD 指标的策略。
