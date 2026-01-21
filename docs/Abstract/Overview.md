# Beruto Project Overview (2026-01-18)

This document summarizes the current state of the Beruto repository to help future AI coding agents quickly regain context.

## Architecture
- App entry: `src/main.py` 鈥?launches PyQt UI by default; `--cli` flag runs a minimal CLI.
- UI client: `src/ui` 鈥?PyQt6 desktop app with panels for symbols and K-line visualization, console, and plan creation/open/close.
- Backtest engine:
  - Python skeleton: `src/backtest` 鈥?conceptual classes for `Context`, `DataProxy`, `BacktestEngine`, `datatype` definitions; largely placeholders.
  - Native core: `src/backtest/engine/src` 鈥?C++ `ChronoEngine` exposed via PyBind11 as `Beruto_core` with T+1 handling and simple buy/sell based on signals.
  - Wrapper: `src/backtest/engine/wrapper/__init__.py` 鈥?loads built extension or falls back to build paths.
- System CLI: `src/system/CLI.py` 鈥?simple REPL (help/echo/exit).
- Data & plans: `data/` and `plan/` 鈥?caches for symbols and K-line; plan JSON defaults and examples; `PlanWizard` builds plans.

## Current Capabilities
- UI
  - File menu with New/Open/Save/Close Plan; New Plan opens `PlanWizard` and auto-opens saved plan; Open Plan loads JSON and shows summary; Close Plan clears summary.
  - Symbols panel for saved codes; K-line panel displays daily candlesticks using AkShare and PyQtGraph with local CSV cache.
  - Console panel wired to CLI for simple text commands.
- Engine
  - C++ `ChronoEngine::run(prices, signals)` returns equity curve; accounts/positions managed with T+1 sellable shares and simple commission/slippage.
  - Python backtest classes are scaffolds and not integrated with UI.

## Key Gaps
- Python backtest (`Context`, `DataProxy`, `BacktestEngine`, `Factor` base) are conceptual and need full implementations and integration.
- No end-to-end pipeline connecting `Plan` -> factors -> signals -> C++ engine -> results in UI.
- Save Plan feature is a placeholder.

## Notable Paths
- UI entry: `src/ui/app.py` 鈫?`MainWindow` in `src/ui/views/main_window.py`
- Plan wizard: `src/ui/views/plan_wizard.py`
- K-line panel: `src/ui/views/kline_panel.py`
- Engine core: `src/backtest/engine/src` (C++) and `src/backtest/engine/wrapper/__init__.py`
- Data caches: `data/kline/*.csv`, `data/symbols_a.csv`, `data/plan_defaults.json`

