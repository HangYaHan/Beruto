# SRC_OVERVIEW

本文档记录当前 `src` 目录每个 Rust 文件的职责（基于当前代码状态）。

## 根模块

- `src/main.rs`
  - 可执行入口。
  - 启动 CLI REPL（`cli::run_repl`），发生错误时打印并退出。

- `src/lib.rs`
  - 库入口。
  - 导出 `backtest`、`data`、`strategy` 三个模块。

## CLI 模块

- `src/cli/mod.rs`
  - CLI 主控制器。
  - 负责 REPL 循环、命令分发、命令实现（fetch/backtest/run/leaderboard/clean）。
  - 包含批量任务计划解析、任务展开、执行与 summary 保存逻辑。

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
  - 计算总收益率与最大回撤。

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
  - 若指定 symbol 对应文件不存在，会触发在线拉取。

- `src/data/fetcher.rs`
  - 在线数据拉取实现。
  - 调用 EastMoney 接口获取日线数据并写入 CSV。
  - 包含代码规范化、市场前缀映射、基本校验。

- `src/data/storage.rs`
  - 回测结果存储与加载。
  - 管理 `.beruto/results` 目录。
  - 保存单次 run 记录、加载历史记录、清理结果文件。

## 策略模块

- `src/strategy/mod.rs`
  - 策略注册与构建中心。
  - 定义策略元信息（`StrategySpec`）与运行配置（`StrategyConfig`）。
  - 根据配置构造具体策略实例。

- `src/strategy/base.rs`
  - 策略抽象层。
  - 定义 `Signal` 枚举和 `Strategy` trait。

- `src/strategy/contrarian.rs`
  - 策略实现。
  - 包含 `BuyAndHoldStrategy` 与 `ContrarianStrategy`。
  - `ContrarianStrategy` 支持阈值配置。
