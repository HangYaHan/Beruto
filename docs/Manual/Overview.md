# 包结构概览

本目录按子模块记录 `src` 包的公共接口。每份手册列出可调用的函数、类和方法，简要说明用途，便于复用和扩展。

## 子包
- `backtest`：任务加载、策略加载与回测编排入口。
- `common`：配置、文件系统与解析类通用工具。
- `data`：数据抓取器、适配器、缓存读写与数据相关异常。
- `execution`：券商接口抽象层。
- `ploter`：OHLC 绘图与指标叠加，包含 CLI 参数解析。
- `portfolio`：组合状态管理与应用策略订单的回测执行。
- `risk`：风控占位，预留订单检查与敞口管理。
- `strategy`：指标计算、触发器 DSL、示例 SMA 金叉死叉策略。
- `system`：日志、JSON 工具、CLI 入口以及（占位的）GUI 主窗口。

## 入口
- CLI：运行 `python -m src.system.CLI` 进入交互循环；`backtest` 命令调用 `src.backtest.engine.run_task`，`plot` 命令调用 `src.ploter.ploter.run_plot_command`。
- 编程式回测：调用 `src.backtest.engine.run_task(task_name)` 读取任务 JSON 并执行回测。
- 绘图：直接使用 `src.ploter.ploter.plot_kline(df, symbol, ...)` 绘制，或用 `run_plot_command(args)` 走 CLI 解析。
- 数据访问：调用 `src.data.fetcher.get_history(symbol, start, end, source, ...)` 获取带缓存的历史行情。
- JSON 工具：`src.system.json.read_json` / `write_json` / `safe_loads` / `safe_dumps` 用于配置与任务 IO。
