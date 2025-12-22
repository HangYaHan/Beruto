"""Unified plotting interface for candlestick charts.

Functions:
	- plot_kline(df, symbol, frame, output, ma)
	- run_plot_command(args): parse CLI args and dispatch plotting

The module normalizes column names to Open/High/Low/Close/Volume when possible.
"""

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import dates as mdates
from src.system.log import get_logger
from src.system.startup import new_result_run_dir
from src.strategy.calc_lines import MA, EMA, RSI, MACD, BOLL, ATR, SUPPORT_LINE, RESISTANCE_LINE

logger = get_logger(__name__)

_COL_MAP = {
	'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume',
	# Common alternative names
	'adj close': 'Close', 'close_adj': 'Close', 'price': 'Close'
}

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
	rename_map = {}
	for c in df.columns:
		key = c.lower()
		if key in _COL_MAP:
			rename_map[c] = _COL_MAP[key]
		elif c in _COL_MAP:
			rename_map[c] = _COL_MAP[c]
	if rename_map:
		df = df.rename(columns=rename_map)
	return df

def _resample(df: pd.DataFrame, frame: str) -> pd.DataFrame:
	if frame == 'weekly':
		if not isinstance(df.index, pd.DatetimeIndex):
			try:
				df.index = pd.to_datetime(df.index)
			except Exception:
				return df  # give up resampling if cannot parse
		agg = {
			'Open': 'first',
			'High': 'max',
			'Low': 'min',
			'Close': 'last',
		}
		if 'Volume' in df.columns:
			agg['Volume'] = 'sum'
		dfw = df.resample('W').agg(agg).dropna(how='any')
		return dfw
	return df

def plot_kline(
	df: pd.DataFrame,
	symbol: str,
	frame: str = 'daily',
	output: str | None = None,
	ma: list[int] | None = None,
	ema: list[int] | None = None,
	boll: tuple[int, float] | None = None,
	rsi: list[int] | None = None,
	macd: tuple[int, int, int] | None = None,
	atr: int | None = None,
	support_breakout: tuple[int, float] | None = None,
    trades: pd.DataFrame | None = None,
) -> None:
	if df is None or df.empty:
		raise ValueError('Empty DataFrame provided to plot_kline')
	df = _normalize_columns(df)
	needed = {'Open','High','Low','Close'}
	missing = needed - set(df.columns)
	if missing:
		raise ValueError(f'Missing columns for candlestick plotting: {missing}')

	df = df.sort_index()
	df = _resample(df, frame)

	# figure size: adapt width to number of bars (approx 1 inch per 10 bars, clamped 12–24)
	n_bars = max(1, len(df))

	# determine indicator panels
	indicator_types = []
	if rsi:
		indicator_types.append('rsi')
	if macd:
		indicator_types.append('macd')
	if atr:
		indicator_types.append('atr')
	logger.info(
		"Plot panels: overlays ma=%s ema=%s boll=%s support_breakout=%s; indicators rsi=%s macd=%s atr=%s",
		ma, ema, boll, support_breakout, rsi, macd, atr,
	)

	n_panels = 1 + len(indicator_types)
	height_ratios = [3] + [1] * len(indicator_types)
	# enlarge figure height when multiple panels; constrained_layout helps keep panels visible in interactive window
	fig_height = 6 if n_panels == 1 else 5 + 3 * len(indicator_types)
	fig, axes = plt.subplots(
		n_panels,
		1,
		sharex=True,
		figsize=(max(12.0, min(24.0, n_bars / 10.0)), fig_height),
		gridspec_kw={'height_ratios': height_ratios},
		constrained_layout=True,
	)
	if n_panels == 1:
		axes = [axes]
	ax = axes[0]
	indicator_axes = list(axes[1:])
	ax.set_title(f'{symbol} {frame} Candlesticks ({len(df)} bars)')
	ax.set_xlabel('Date')
	ax.set_ylabel('Price')

	if not isinstance(df.index, pd.DatetimeIndex):
		try:
			df.index = pd.to_datetime(df.index)
		except Exception as e:
			logger.warning('Failed to convert index to datetime: %s', e)

	dates = df.index.to_pydatetime()

	# width of each candle (days). For weekly change, widen a bit.
	width = 0.6 if frame != 'weekly' else 3.2

	for i, (ts, row) in enumerate(df.iterrows()):
		o = float(row['Open']); h = float(row['High']); l = float(row['Low']); c = float(row['Close'])
		color = 'red' if c >= o else 'green'
		# wick
		ax.vlines(ts, l, h, color=color, linewidth=1)
		# body
		body_low = min(o, c)
		body_height = abs(c - o)
		if body_height == 0:
			# draw a very thin line to represent no change
			ax.hlines(o, ts, ts, color=color, linewidth=2)
		else:
			rect = Rectangle((ts, body_low), pd.Timedelta(days=width), body_height, facecolor=color, edgecolor=color, linewidth=0.5)
			ax.add_patch(rect)

	# Use automatic, concise date ticks to avoid clutter
	locator = mdates.AutoDateLocator(minticks=6, maxticks=10)
	formatter = mdates.ConciseDateFormatter(locator)
	ax.xaxis.set_major_locator(locator)
	ax.xaxis.set_major_formatter(formatter)
	# Add a bit of margin to keep markers from touching borders
	ax.margins(x=0.01, y=0.05)

	if 'Volume' in df.columns:
		ax2 = ax.twinx()
		ax2.set_ylabel('Volume')
		try:
			ax2.bar(dates, df['Volume'].values, alpha=0.15, color='gray')
		except Exception:
			pass

	# Moving averages / overlays
	if ma:
		for w in ma:
			try:
				series = MA(df['Close'], w)
				ax.plot(dates, series.values, linewidth=1.2, label=f'MA{w}')
			except Exception:
				logger.warning('Failed to compute MA%s', w)

	if ema:
		for w in ema:
			try:
				series = EMA(df['Close'], w)
				ax.plot(dates, series.values, linewidth=1.2, linestyle='--', label=f'EMA{w}')
			except Exception:
				logger.warning('Failed to compute EMA%s', w)

	if boll:
		try:
			win, k = boll
			bands = BOLL(df['Close'], window=win, k=k)
			ax.plot(dates, bands['mid'].values, color='purple', linewidth=1.0, label=f'BOLL{win}')
			ax.plot(dates, bands['upper'].values, color='purple', linewidth=0.8, linestyle='--')
			ax.plot(dates, bands['lower'].values, color='purple', linewidth=0.8, linestyle='--')
		except Exception:
			logger.warning('Failed to compute BOLL with %s', boll)

	if support_breakout:
		try:
			win, temp = support_breakout
			support_line = SUPPORT_LINE(df['Close'], window=win, temperature=temp)
			resist_line = RESISTANCE_LINE(df['Close'], window=win, temperature=temp)
			ax.plot(dates, support_line.values, color='#1f77b4', linewidth=1.0, linestyle='-.', label=f'Support{win}@{temp}')
			ax.plot(dates, resist_line.values, color='#ff7f0e', linewidth=1.0, linestyle='-.', label=f'Resist{win}@{temp}')
		except Exception:
			logger.warning('Failed to compute support/resistance with %s', support_breakout)

	# Legend for price panel if any overlay exists
	handles, labels = ax.get_legend_handles_labels()
	if handles:
		ax.legend(loc='upper left', fontsize=8)

	# Annotate trades (buy/sell markers)
	if trades is not None and not trades.empty:
		try:
			tr = trades.copy()
			tr['date'] = pd.to_datetime(tr['date'])
			tr = tr.sort_values('date')
			# filter current symbol only if symbol column exists
			if 'symbol' in tr.columns:
				tr = tr[tr['symbol'] == symbol]
			# align to plotting index range
			min_dt = pd.to_datetime(df.index.min())
			max_dt = pd.to_datetime(df.index.max())
			tr = tr[(tr['date'] >= min_dt) & (tr['date'] <= max_dt)]
			if not tr.empty:
				# fetch price at trade date (use Close)
				close_series = df['Close']
				buy_mask = (tr.get('side', '').astype(str).str.upper() == 'BUY') | (tr.get('qty', 0) > 0)
				sell_mask = (tr.get('side', '').astype(str).str.upper() == 'SELL') | (tr.get('qty', 0) < 0)
				buy_dt = tr.loc[buy_mask, 'date']
				sell_dt = tr.loc[sell_mask, 'date']
				buy_px = []
				sell_px = []
				for d in buy_dt:
					# use nearest available index on/ before date
					idx = close_series.loc[:d]
					buy_px.append(float(idx.iloc[-1]) if not idx.empty else None)
				for d in sell_dt:
					idx = close_series.loc[:d]
					sell_px.append(float(idx.iloc[-1]) if not idx.empty else None)
				buy_dt_plot = [d for d, p in zip(buy_dt, buy_px) if p is not None]
				buy_px_plot = [p for p in buy_px if p is not None]
				sell_dt_plot = [d for d, p in zip(sell_dt, sell_px) if p is not None]
				sell_px_plot = [p for p in sell_px if p is not None]
				# Use more explicit markers and colors
				if buy_dt_plot:
					ax.scatter(
						buy_dt_plot,
						buy_px_plot,
						marker='^',
						facecolors='#2ca02c',  # vivid green
						edgecolors='black',
						s=64,
						alpha=0.9,
						label='BUY'
					)
				if sell_dt_plot:
					ax.scatter(
						sell_dt_plot,
						sell_px_plot,
						marker='v',
						facecolors='#d62728',  # vivid red
						edgecolors='black',
						s=64,
						alpha=0.9,
						label='SELL'
					)
				# ensure legend includes BUY/SELL
				handles2, labels2 = ax.get_legend_handles_labels()
				if handles2:
					ax.legend(loc='upper left', fontsize=8)
		except Exception as e:
			logger.warning('Failed to annotate trades: %s', e)

	# Indicator panel
	# draw indicators, one panel per type
	for idx, ind_type in enumerate(indicator_types):
		ax_i = indicator_axes[idx]
		if ind_type == 'rsi' and rsi:
			for w in rsi:
				try:
					series = RSI(df['Close'], w)
					ax_i.plot(dates, series.values, linewidth=1.0, label=f'RSI{w}')
				except Exception:
					logger.warning('Failed to compute RSI%s', w)
			ax_i.axhline(70, color='gray', linestyle='--', linewidth=0.8)
			ax_i.axhline(30, color='gray', linestyle='--', linewidth=0.8)
			ax_i.set_ylabel('RSI')

		if ind_type == 'macd' and macd:
			try:
				fast, slow, signal = macd
				macd_df = MACD(df['Close'], fast=fast, slow=slow, signal=signal)
				ax_i.bar(dates, macd_df['hist'].values, color='gray', alpha=0.3, label='MACD hist')
				ax_i.plot(dates, macd_df['macd'].values, color='blue', linewidth=1.0, label='MACD')
				ax_i.plot(dates, macd_df['signal'].values, color='orange', linewidth=1.0, label='Signal')
			except Exception:
				logger.warning('Failed to compute MACD with %s', macd)
			ax_i.set_ylabel('MACD')

		if ind_type == 'atr' and atr:
			try:
				series = ATR(df['High'], df['Low'], df['Close'], window=atr)
				ax_i.plot(dates, series.values, linewidth=1.0, label=f'ATR{atr}')
			except Exception:
				logger.warning('Failed to compute ATR%s', atr)
			ax_i.set_ylabel('ATR')

		handles_i, labels_i = ax_i.get_legend_handles_labels()
		if handles_i:
			ax_i.legend(loc='upper left', fontsize=8)

	if output:
		try:
			fig.savefig(output, dpi=180, bbox_inches='tight')
			logger.info('Saved plot to %s', output)
		except Exception as e:
			logger.exception('Failed saving plot: %s', e)
			raise
	else:
		# Default to saving in a result run directory
		run_dir = new_result_run_dir()
		out_path = run_dir / f"plot_{symbol}_{frame}.png"
		try:
			fig.savefig(out_path, dpi=180, bbox_inches='tight')
			logger.info('Saved plot to %s', out_path)
		except Exception as e:
			logger.exception('Failed saving default plot: %s', e)
			raise

	plt.close(fig)

def run_plot_command(args: list[str]) -> None:
	"""Parse CLI args and execute plotting.

	Supported:
	  plot SYMBOL [-start YYYYMMDD] [-end YYYYMMDD]
		   [-frame daily|weekly] [-source akshare|yfinance|csv]
		   [-refresh] [-output file.png]
		   [-ma 5,20] [-ema 12,26] [-boll 20,2]
		   [-rsi 14] [-macd 12,26,9] [-atr 14]
	"""
	from src.data import fetcher as data_fetcher

	if not args:
		print("Usage: plot SYMBOL [-start YYYYMMDD] [-end YYYYMMDD] [-frame daily|weekly] [-source akshare|yfinance|csv] [-refresh] [-output file.png] [-ma 5,20] [-ema 12,26] [-boll 20,2] [-rsi 14] [-macd 12,26,9] [-atr 14] [-sr window,temp]")
		return

	symbol = args[0]
	start = None
	end = None
	frame = 'daily'
	source = 'akshare'
	refresh = False
	output = None
	ma_list: list[int] | None = None
	ema_list: list[int] | None = None
	boll_params: tuple[int, float] | None = None
	rsi_list: list[int] | None = None
	macd_params: tuple[int, int, int] | None = None
	atr_window: int | None = None
	sr_params: tuple[int, float] | None = None

	i = 1
	while i < len(args):
		tok = args[i]
		if tok == '-start' and i + 1 < len(args):
			start = args[i+1]; i += 2; continue
		if tok == '-end' and i + 1 < len(args):
			end = args[i+1]; i += 2; continue
		if tok == '-frame' and i + 1 < len(args):
			frame = args[i+1].lower(); i += 2; continue
		if tok == '-source' and i + 1 < len(args):
			source = args[i+1].lower(); i += 2; continue
		if tok == '-output' and i + 1 < len(args):
			output = args[i+1]; i += 2; continue
		if tok == '-refresh':
			refresh = True; i += 1; continue
		if tok == '-ma' and i + 1 < len(args):
			raw = args[i+1]
			try:
				ma_list = [int(x.strip()) for x in raw.split(',') if x.strip()]
			except Exception:
				print(f"Invalid -ma value: {raw}")
			i += 2; continue
		if tok == '-ema' and i + 1 < len(args):
			raw = args[i+1]
			try:
				ema_list = [int(x.strip()) for x in raw.split(',') if x.strip()]
			except Exception:
				print(f"Invalid -ema value: {raw}")
			i += 2; continue
		if tok == '-boll' and i + 1 < len(args):
			raw = args[i+1]
			parts = [x.strip() for x in raw.split(',') if x.strip()]
			if len(parts) == 2:
				try:
					boll_params = (int(parts[0]), float(parts[1]))
				except Exception:
					print(f"Invalid -boll value: {raw}")
			else:
				print(f"Invalid -boll value: {raw}")
			i += 2; continue
		if tok == '-rsi' and i + 1 < len(args):
			raw = args[i+1]
			try:
				rsi_list = [int(x.strip()) for x in raw.split(',') if x.strip()]
			except Exception:
				print(f"Invalid -rsi value: {raw}")
			i += 2; continue
		if tok == '-macd' and i + 1 < len(args):
			raw = args[i+1]
			parts = [x.strip() for x in raw.split(',') if x.strip()]
			if len(parts) == 3:
				try:
					macd_params = (int(parts[0]), int(parts[1]), int(parts[2]))
				except Exception:
					print(f"Invalid -macd value: {raw}")
			else:
				print(f"Invalid -macd value: {raw}")
			i += 2; continue
		if tok == '-atr' and i + 1 < len(args):
			try:
				atr_window = int(args[i+1])
			except Exception:
				print(f"Invalid -atr value: {args[i+1]}")
			i += 2; continue
		if tok == '-sr' and i + 1 < len(args):
			raw = args[i+1]
			parts = [x.strip() for x in raw.split(',') if x.strip()]
			if len(parts) == 2:
				try:
					sr_params = (int(parts[0]), float(parts[1]))
				except Exception:
					print(f"Invalid -sr value: {raw}")
			else:
				print(f"Invalid -sr value: {raw}")
			i += 2; continue
		print(f"Unknown arg: {tok}")
		i += 1

	try:
		df = data_fetcher.get_history(symbol, start, end, source=source, interval='1d', cache=True, refresh=refresh)
	except Exception as e:
		logger.exception("Failed to fetch data for plot: %s", e)
		print(f"Failed to fetch data: {e}")
		return

	if df is None or df.empty:
		print(f"No data to plot for {symbol}.")
		return

	try:
		plot_kline(
			df,
			symbol=symbol,
			frame=frame,
			output=output,
			ma=ma_list,
			ema=ema_list,
			boll=boll_params,
			rsi=rsi_list,
			macd=macd_params,
			atr=atr_window,
			support_breakout=sr_params,
		)
		if output:
			print(f"Plotted {symbol} ({frame}) rows={len(df)} -> {output}")
		else:
			print(f"Plotted {symbol} ({frame}) rows={len(df)} -> saved to result run directory")
	except Exception as e:
		logger.exception("Plotting failed for %s: %s", symbol, e)
		print(f"Plot failed: {e}")


__all__ = ['plot_kline', 'run_plot_command']