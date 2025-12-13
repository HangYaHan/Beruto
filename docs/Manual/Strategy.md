# strategy

来源：`src/strategy/calc_lines.py`，`src/strategy/support.py`，`src/strategy/yahan_strategies.py`

## calc_lines（指标工具）
- `CLOSE/OPEN/HIGH/LOW/VOLUME(df: pandas.DataFrame) -> pandas.Series`：按常见列名（不区分大小写）取值，否则抛出 `KeyError`。
- `LAG(series: SeriesLike, n: int = 1) -> SeriesLike`：向后平移 `n`。
- `DIFF(series: SeriesLike, n: int = 1) -> SeriesLike`：与前 `n` 期的差分。
- `ROLLING_MAX/MIN(series: SeriesLike, window: int) -> SeriesLike`：滚动极值，`min_periods=1`。
- `STD(series, window)`，`ZSCORE(series, window)`：滚动标准差与 z-score。
- `MA(series, window)`，`EMA(series, window)`：均线与指数均线。
- `RSI(series, window: int = 14) -> SeriesLike`：基于涨跌幅 EMA 的 RSI。
- `MACD(series, fast: int = 12, slow: int = 26, signal: int = 9) -> pandas.DataFrame`：列包含 `macd`、`signal`、`hist`。
- `BOLL(series, window: int = 20, k: float = 2.0) -> pandas.DataFrame`：列包含 `mid`、`upper`、`lower`。
- `ATR(high, low, close, window: int = 14) -> SeriesLike`：真实波动幅度均值。
- `RESAMPLE_OHLC(df, rule: str) -> pandas.DataFrame`：按周期重采样 OHLC(+Volume) 数据，要求 DatetimeIndex。
- `RESAMPLE(series, rule: str, how: str = 'last'|'first'|'mean') -> SeriesLike`：按周期重采样 Series。

## support（触发器 DSL）
- `class Trigger(condition, action, name: str | None = None)`：评估条件并在上升沿触发动作。
  - `evaluate(context) -> None`：执行条件与动作，并进行错误包装。
- `always(condition, action, name=None) -> Trigger`：注册全局触发器。
- `on_bar(action) -> action`：注册每根 K 线回调。
- `run_triggers(context) -> None`：先运行所有 on_bar，再运行触发器。
- `assign(value) -> Any`：恒等辅助函数。
- `assert_stmt(condition: bool, message: str = 'assertion failed') -> None`：条件为假时抛出 `AssertionError`。
- `crossabove(a: pandas.Series, b: pandas.Series) -> pandas.Series`：在当前 K 线上 `a` 上穿 `b` 时为真。
- `crossbelow(a: pandas.Series, b: pandas.Series) -> pandas.Series`：在当前 K 线上 `a` 下穿 `b` 时为真。

## yahan_strategies（示例）
- `class SMAStrategy`：
  - `__init__(self, symbol: str, short_window: int = 5, long_window: int = 20, qty: int = 100)`：配置标的和均线窗口。
  - `decide(self, date: pandas.Timestamp, history: pandas.DataFrame) -> dict[str, int]`：用 `MA` 与 `crossabove/crossbelow` 计算金叉/死叉信号；返回订单字典（买为正、卖为负），无信号则返回空字典。
