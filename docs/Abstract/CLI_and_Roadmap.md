# CLI & Roadmap Summary

## CLI
- Entry: `src/system/CLI.py`.
- Commands: `help`, `echo <text>`, `exit` (+ two easter eggs).
- Purpose: minimal REPL; UI console proxies `execute_command()` and prints outputs.

## Roadmap (High-Level)
- Backtest Python → Implement `Context`, `DataProxy`, and `BacktestEngine` per pseudocode; wire to AkShare or local caches, ensure no look-ahead.
- Factors → Finish `Factor` base and add concrete factor implementations; expose in UI factor selection and params editing.
- Signals → Build matrix generation from factors and universe; define fusion logic per `Arbiter` (linear/conditional/AI) to produce per-symbol signals.
- Engine Integration → Bridge signals and price matrices into `ChronoEngine::run`; collect equity curve and key metrics; persist results.
- UI Results → Add tabs for Signals/Portfolio/Orders with real data; draw equity curve and performance stats; add run/backtest controls.
- Plans → Complete Save Plan logic and plan editing; add plan application to backtests.
- Packaging → Ensure robust extension loading across dev/build environments.

## Open Questions
- Data source stability (AkShare) vs building robust local pipeline.
- T+1 rules and real-world edge cases (e.g., limit up/down handling) in native core.
- AI model support for `Arbiter` (pretrained model loading and inference path).
