# ploter

来源：`src/ploter/ploter.py`

## 函数
- `plot_kline(df: pandas.DataFrame, symbol: str, frame: str = 'daily', output: str | None = None, ma: list[int] | None = None, ema: list[int] | None = None, boll: tuple[int, float] | None = None, rsi: list[int] | None = None, macd: tuple[int, int, int] | None = None, atr: int | None = None) -> None`：绘制带叠加指标的蜡烛图，可将输出保存到文件（传入 `output`）或直接展示。
- `run_plot_command(args: list[str]) -> None`：解析 CLI 参数（`plot SYMBOL [-start ...] [-end ...] [-frame daily|weekly] [-source ...] [-refresh] [-output file.png] [-ma ...] [-ema ...] [-boll win,k] [-rsi win] [-macd f,s,signal] [-atr win]`），调用 `data.fetcher.get_history` 获取数据，再交给 `plot_kline` 绘图。

## 行为
- 将列名规范化为 `Open/High/Low/Close/Volume`，缺少 OHLC 会报错。
- 当 `frame='weekly'` 且索引为时间时，会重采样为周线。
- 支持的指标：MA、EMA、布林、RSI、MACD、ATR；有成交量时叠加成交量。
