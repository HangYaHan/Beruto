# backtest

来源：`src/backtest/engine.py`

## 函数
- `load_task(task_name: str) -> dict`：读取任务 JSON（`tasks/{task_name}.json`），返回解析后的字典。
- `load_strategy(module_path: str, class_name: str, params: dict) -> Any`：动态导入模块并用参数实例化策略类。
- `run_task(task_name: str) -> pandas.DataFrame`：高级入口，依次加载任务、调用 `data.fetcher.get_history` 拉取行情、用 `load_strategy` 创建策略，再交给 `portfolio.manager.run_backtest` 回测，返回权益曲线 DataFrame。

## 说明
- 任务 JSON 预期字段：`symbol`、`start`、`end`、`strategy` 块，以及可选的 `source`、`commission`、`slippage`、`initial_cash`。
- 错误会向上传递；CLI 层负责捕获并打印。
