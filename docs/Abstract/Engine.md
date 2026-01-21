# Backtest Engine Summary

## Native Core (C++)
- Module: `Beruto_core` via PyBind11.
- Class: `ChronoEngine(initial_cash)` with `run(prices, signals)` 鈫?returns equity curve (`numpy` array). Shapes required: both 2D, same shape `(n_days, n_stocks)`.
- Logic:
  - T+1: new buys are not sellable until next day; pre-market step unlocks previous-day buys.
  - Signals: `sig > 0` buys proportional to intent; `sig < 0` sells proportional within sellable shares.
  - Costs: commission/slippage constants (0.03% each) applied on buy/sell.
  - Account equity computed as cash + sum(position shares 脳 price) per day.
- Structures: `Account` and `Position` (avg cost, total/sellable shares) in `account.h`.

## Python Wrapper
- `src/backtest/engine/wrapper/__init__.py`: loads `Beruto_core`, attempts build lib directories if direct import fails, and can load `.pyd` explicitly.
- `build/lib.*` contains a packaged `wrapper/__init__.py` mirroring lazy import for distribution.

## Python Backtest Skeleton
- Files: `src/backtest/core.py`, `src/backtest/context.py`, `src/backtest/datatype.py`, `src/backtest/feed.py`.
- Purpose: define conceptual classes and datatypes (`AccountState`, `Position`, `BarData`, `Order`) and the pluggable `DataProxy`.
- Status: methods contain pseudocode and `pass`; no integration with UI or C++ core.

## Integration Status
- No pipeline from plan JSON 鈫?factor evaluation 鈫?signals 鈫?`ChronoEngine` yet.
- Missing: factor implementations, data adapter to produce `prices`/`signals` matrices, and UI hooks to run backtests.

