# system

来源：`src/system/CLI.py`，`src/system/json.py`，`src/system/log.py`，`src/system/main_window.py`

## CLI
- `print_help() -> None`：打印 CLI 帮助文本。
- `interactive_loop() -> int`：简易 REPL，支持 `help`、`exit`、`backtest TASK`、`config`、`plot ...`，并委托到回测/绘图模块。
- `main(argv: list[str] | None = None) -> int`：`interactive_loop` 的入口包装，带错误处理。

## json 工具
- `read_json(path: str | Path, default: Any | None = None) -> Any`：读取 JSON；缺失或解析失败返回 `default`。
- `write_json(path: str | Path, data: Any, *, indent: int = 2, ensure_ascii: bool = False) -> None`：写入 JSON，自动创建父目录；发生错误会记录日志并继续抛出。
- `safe_loads(s: str, default: Any | None = None) -> Any`：解析 JSON 字符串，失败返回 `default`。
- `safe_dumps(obj: Any, *, indent: int = 2, ensure_ascii: bool = False) -> str`：将对象序列化为 JSON 字符串。

## log
- `configure_root_logger(level=logging.INFO) -> None`：幂等的根日志配置，输出到 `logs/` 下的时间戳文件，并移除控制台 handler。
- `get_logger(name: str | None = None) -> logging.Logger`：确保根日志器已配置，然后返回指定日志器。

## main_window
- 占位文件，暂无实现。
