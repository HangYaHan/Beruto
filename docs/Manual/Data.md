# data

来源：`src/data/fetcher.py`，`src/data/storage.py`，`src/data/exceptions.py`，`src/data/adapters/*.py`

## fetcher
- `select_adapter(name: str) -> Callable`：把适配器名称（`akshare`、`yfinance`、`csv`）映射到具体抓取函数，未知名称会抛出 `AdapterError`。
- `get_history(symbol: str, start: str | None, end: str | None, *, source: str = 'akshare', interval: str = '1d', adjusted: bool = True, cache: bool = True, refresh: bool = False) -> pandas.DataFrame`：通过适配器获取历史 OHLCV，可选用 parquet 缓存；`refresh=True` 强制绕过缓存，成功后会写回缓存。
- `valid_test() -> pandas.DataFrame | None`：抓取示例标的的快速冒烟测试。

## storage
- `_cache_path(symbol: str) -> pathlib.Path`：内部工具，计算 `data/` 下的 parquet 缓存路径。
- `write_cache(symbol: str, df: pandas.DataFrame) -> None`：将 DataFrame 保存为 parquet 缓存（会创建父目录）。
- `read_cached(symbol: str, start: str | None = None, end: str | None = None) -> pandas.DataFrame | None`：读取缓存并按需要按日期切片，缺失时返回 `None`。

## exceptions
- `DataFetchError`、`RateLimitError`、`DataNotFoundError`、`AdapterError`、`NetworkError`：数据层的领域异常。

## adapters
- `akshare_adapter.fetch(symbol: str, start: str | None, end: str | None, interval: str = '1d', adjusted: bool = True, **kwargs) -> pandas.DataFrame`：通过 `akshare` 抓取，转换类型并设置时间索引，返回 OHLCV。
- `yfinance_adapter.fetch(symbol: str, start: str | None, end: str | None, interval: str = '1d', adjusted: bool = True, **kwargs) -> pandas.DataFrame`：通过 `yfinance.download` 抓取，返回带时间索引的 OHLCV。
- `csv_adapter.fetch(symbol: str, start: str | None, end: str | None, interval: str = '1d', **kwargs) -> pandas.DataFrame`：读取本地 CSV（路径来自 `kwargs['path']`），解析日期并重命名为 OHLCV，缺少路径会报错。
