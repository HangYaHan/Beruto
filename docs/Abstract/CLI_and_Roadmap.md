# CLI & Roadmap Summary

## CLI
- Entry: `src/system/CLI.py`.
- Commands: `help`, `echo <text>`, `exit` (+ two easter eggs).
- Purpose: minimal REPL; UI console proxies `execute_command()` and prints outputs.

## Roadmap (High-Level)
- Backtest Python 鈫?Implement `Context`, `DataProxy`, and `BacktestEngine` per pseudocode; wire to AkShare or local caches, ensure no look-ahead.
- Factors 鈫?Finish `Factor` base and add concrete factor implementations; expose in UI factor selection and params editing.
- Signals 鈫?Build matrix generation from factors and universe; define fusion logic per `Scoring` (linear/conditional/AI) to produce per-symbol signals.
- Engine Integration 鈫?Bridge signals and price matrices into `ChronoEngine::run`; collect equity curve and key metrics; persist results.
- UI Results 鈫?Add tabs for Signals/Portfolio/Orders with real data; draw equity curve and performance stats; add run/backtest controls.
- Plans 鈫?Complete Save Plan logic and plan editing; add plan application to backtests.
- Packaging 鈫?Ensure robust extension loading across dev/build environments.

## Open Questions
- Data source stability (AkShare) vs building robust local pipeline.
- T+1 rules and real-world edge cases (e.g., limit up/down handling) in native core.
- AI model support for `Scoring` (pretrained model loading and inference path).

