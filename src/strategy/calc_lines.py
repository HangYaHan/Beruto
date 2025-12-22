"""Core time-series helper functions for strategy building.

All functions operate on pandas Series/DataFrame and stay ASCII-only.
"""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

SeriesLike = pd.Series


def _pick_col(df: pd.DataFrame, candidates: Iterable[str]) -> pd.Series:
	lower_cols = {c.lower(): c for c in df.columns}
	for name in candidates:
		key = name.lower()
		if key in lower_cols:
			return df[lower_cols[key]]
	raise KeyError(f"No column found among candidates: {list(candidates)}")


def CLOSE(df: pd.DataFrame) -> SeriesLike:
	return _pick_col(df, ["close", "adj close", "adj_close", "price"])


def OPEN(df: pd.DataFrame) -> SeriesLike:
	return _pick_col(df, ["open"])


def HIGH(df: pd.DataFrame) -> SeriesLike:
	return _pick_col(df, ["high"])


def LOW(df: pd.DataFrame) -> SeriesLike:
	return _pick_col(df, ["low"])


def VOLUME(df: pd.DataFrame) -> SeriesLike:
	return _pick_col(df, ["volume", "vol"])


def LAG(series: SeriesLike, n: int = 1) -> SeriesLike:
	return series.shift(n)


def DIFF(series: SeriesLike, n: int = 1) -> SeriesLike:
	return series.diff(n)


def ROLLING_MAX(series: SeriesLike, window: int) -> SeriesLike:
	return series.rolling(window, min_periods=1).max()


def ROLLING_MIN(series: SeriesLike, window: int) -> SeriesLike:
	return series.rolling(window, min_periods=1).min()


def STD(series: SeriesLike, window: int) -> SeriesLike:
	return series.rolling(window, min_periods=1).std()


def ZSCORE(series: SeriesLike, window: int) -> SeriesLike:
	rolling_mean = series.rolling(window, min_periods=1).mean()
	rolling_std = series.rolling(window, min_periods=1).std()
	return (series - rolling_mean) / rolling_std.replace(0, np.nan)


def MA(series: SeriesLike, window: int) -> SeriesLike:
	return series.rolling(window, min_periods=1).mean()


def EMA(series: SeriesLike, window: int) -> SeriesLike:
	return series.ewm(span=window, adjust=False).mean()


def RSI(series: SeriesLike, window: int = 14) -> SeriesLike:
	delta = series.diff()
	gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
	loss = -delta.clip(upper=0).ewm(alpha=1 / window, adjust=False).mean()
	rs = gain / loss.replace(0, np.nan)
	return 100 - (100 / (1 + rs))


def MACD(series: SeriesLike, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
	fast_ema = EMA(series, fast)
	slow_ema = EMA(series, slow)
	macd = fast_ema - slow_ema
	signal_line = EMA(macd, signal)
	hist = macd - signal_line
	return pd.DataFrame({"macd": macd, "signal": signal_line, "hist": hist})


def BOLL(series: SeriesLike, window: int = 20, k: float = 2.0) -> pd.DataFrame:
	mid = MA(series, window)
	dev = STD(series, window)
	upper = mid + k * dev
	lower = mid - k * dev
	return pd.DataFrame({"mid": mid, "upper": upper, "lower": lower})


def ATR(high: SeriesLike, low: SeriesLike, close: SeriesLike, window: int = 14) -> SeriesLike:
	prev_close = close.shift(1)
	tr = pd.concat([
		high - low,
		(high - prev_close).abs(),
		(low - prev_close).abs()
	], axis=1).max(axis=1)
	return tr.rolling(window, min_periods=1).mean()


def SUPPORT_LINE(series: SeriesLike, window: int = 20, temperature: float = 1.0) -> SeriesLike:
	"""Smoothed rolling minimum as support line.

	`temperature` (>0) scales smoothing strength: higher values dampen noise by
	using a longer EWMA span based on `window * temperature`.
	"""
	if temperature <= 0:
		raise ValueError("temperature must be positive")
	raw_support = series.rolling(window, min_periods=1).min()
	span = max(1, int(round(window * temperature)))
	return raw_support.ewm(span=span, adjust=False).mean()


def RESISTANCE_LINE(series: SeriesLike, window: int = 20, temperature: float = 1.0) -> SeriesLike:
	"""Smoothed rolling maximum as resistance/breakout line.

	`temperature` (>0) scales smoothing strength: higher values dampen noise by
	using a longer EWMA span based on `window * temperature`.
	"""
	if temperature <= 0:
		raise ValueError("temperature must be positive")
	raw_resist = series.rolling(window, min_periods=1).max()
	span = max(1, int(round(window * temperature)))
	return raw_resist.ewm(span=span, adjust=False).mean()


def RESAMPLE_OHLC(df: pd.DataFrame, rule: str) -> pd.DataFrame:
	if not isinstance(df.index, pd.DatetimeIndex):
		raise TypeError("DataFrame index must be DatetimeIndex for resampling")
	agg = {
		"Open": "first",
		"High": "max",
		"Low": "min",
		"Close": "last",
	}
	if "Volume" in df.columns:
		agg["Volume"] = "sum"
	return df.resample(rule).agg(agg).dropna(how="any")


def RESAMPLE(series: SeriesLike, rule: str, how: str = "last") -> SeriesLike:
	if not isinstance(series.index, pd.DatetimeIndex):
		raise TypeError("Series index must be DatetimeIndex for resampling")
	if how == "last":
		return series.resample(rule).last()
	if how == "first":
		return series.resample(rule).first()
	if how == "mean":
		return series.resample(rule).mean()
	raise ValueError(f"Unsupported resample aggregation: {how}")


__all__ = [
	"CLOSE",
	"OPEN",
	"HIGH",
	"LOW",
	"VOLUME",
	"LAG",
	"DIFF",
	"ROLLING_MAX",
	"ROLLING_MIN",
	"STD",
	"ZSCORE",
	"MA",
	"EMA",
	"RSI",
	"MACD",
	"BOLL",
	"ATR",
	"RESAMPLE_OHLC",
	"RESAMPLE",
	"SUPPORT_LINE",
	"RESISTANCE_LINE",
]
