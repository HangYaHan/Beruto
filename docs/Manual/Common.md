# common

来源：`src/common/config.py`，`src/common/utils.py`

## config
- `load_config(path: str) -> dict | None`：占位函数，计划用于从文件读取配置。
- `save_config(cfg: dict, path: str) -> None`：占位函数，计划用于将配置持久化到文件。
- `get_config_value(cfg: dict, key: str, default: Any = None) -> Any`：占位函数，计划提供带默认值的安全查找。

## utils
- `ensure_dir(path: str) -> None`：占位函数，计划在目录不存在时创建目录。
- `parse_date(value: str | datetime) -> datetime`：占位函数，计划将输入转换为 `datetime`。
- `chunk_iterable(it: Iterable[T], size: int) -> Iterable[list[T]]`：占位函数，计划按固定大小切分可迭代对象。
