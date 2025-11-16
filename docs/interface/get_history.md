# function: get_history

## 函数签名
````python
def get_history(symbol, start, end, source='yfinance', interval='1d', adjusted=True,
                cache=True, max_retries=3, backoff_factor=1, refresh=False, **kwargs)
````

## 功能概述
- 统一的数据拉取入口。优先从本地缓存读取指定 symbol 的历史 OHLCV 数据；若未命中或强制刷新，则调用对应数据源适配器（adapter.fetch）从远端获取，成功后可写入本地缓存。对速率限制错误（RateLimitError）实现指数退避重试。

## 参数说明
- symbol (str)：标的代码（例如 "AAPL"、"600519.SS" 等）。
- start (str or datetime)：起始日期（可为字符串或 datetime）。
- end (str or datetime)：结束日期。
- source (str, default 'yfinance')：数据源 key，映射到 ADAPTERS（支持 'csv'、'yfinance'）。
- interval (str, default '1d')：数据粒度（如 '1d', '1m' 等，依 adapter 支持）。
- adjusted (bool, default True)：是否返回复权/调整过的价格（由 adapter 支持与实现）。
- cache (bool, default True)：是否使用本地缓存（read_cached / write_cache）。
- refresh (bool, default False)：若为 True 则跳过缓存强制从远端拉取并覆盖缓存。
- max_retries (int, default 3)：在遇到 RateLimitError 时的最大重试次数。
- backoff_factor (int/float, default 1)：指数退避基数，等待秒数计算为 (2**attempt) * backoff_factor。
- **kwargs：传给适配器的额外参数（例如 API key、session 等）。

## 返回值
- 返回 pandas.DataFrame：标准化的时间索引与 OHLCV 列（由具体 adapter 定义和规范化）。
- 如果成功读取到数据则返回非空 DataFrame。

## 异常与行为
- 若 adapter 返回 None 或 空 DataFrame，会抛出 DataNotFoundError。
- 在适配器抛出 RateLimitError 时，函数会按指数退避重试，超过 max_retries 后抛出最后的异常。
- 其他未捕获的异常会在循环外抛出（作为 last_exc）。
- 若指定 source 不存在，会抛出 ValueError。

## 适配器约定
- ADAPTERS 中的每个 adapter 应实现 fetch(symbol, start, end, **kwargs) 并返回 DataFrame，或在错误情况下抛出统一异常（RateLimitError、AdapterError、NetworkError 等）。

## 调用示例
```python
df = get_history("AAPL", "2023-01-01", "2023-06-30", source="yfinance", interval="1d")
```