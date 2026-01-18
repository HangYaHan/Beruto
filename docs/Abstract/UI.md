# UI Summary (PyQt6)

## Main Window
- Menus: File (New/Open/Save/Close Plan, Exit), Help (Show/Hide Console, About).
- Tabs/Panels:
  - Left: Universe (placeholders), Symbols, Factors (placeholders), Plan/Arbiter.
  - Middle: Chart (K-line), Signals/Portfolio/Orders (placeholders).
  - Right: Info Wall (status, risk, tasks — placeholders).
- Console: Text REPL connected to `src/system/CLI.py` with basic commands.

## Plan Handling
- New Plan: opens `PlanWizardDialog`; on successful save, auto-opens the saved JSON plan.
- Open Plan: file dialog filters `*.json`, loads plan, updates summary.
- Close Plan: clears `current_plan` and resets summary label.
- Summary Content: name/created-at, symbol count (first few listed), oracle count, arbiter mode & scheduling, executor initial cash, plan file path.

## Symbols & K-Line Workflow
- Symbol caching: loads `data/symbols_a.csv` or fetches via AkShare (A-shares + ETFs), saved to cache; saved user symbols persisted in `data/saved_symbols.txt`.
- K-Line panel:
  - Download via AkShare (`stock_zh_a_hist` / `fund_etf_hist_em`), normalized columns: date/open/high/low/close[/volume].
  - Local cache CSV per symbol in `data/kline/<code>.csv`.
  - Rendering: PyQtGraph `CandlestickItem`; axis uses date ticks; simple range and padding.
  - Drag-and-drop from symbols to chart supported.

## Plan Wizard
- Pages: Universe (dates, type, symbols), Oracles (factor library, selection, params JSON, preprocess), Arbiter (fusion mode linear/conditional/AI; scheduling; constraints), Executor (cash/fees/slippage), Preserver (metadata & save path).
- Factor library: combines `data/factor.csv` and `data/factors/*.json` defaults; built-ins include `Do_Nothing` and `Buy_&_Hold`.
- Save: writes full plan JSON to chosen path; sets `created_plan_path` on dialog for auto-open.
