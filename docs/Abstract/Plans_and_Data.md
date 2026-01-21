# Plans & Data Summary

## Plan JSON
- Produced by `PlanWizardDialog` with sections:
  - `Universe`: `start_date`, `end_date`, `data_frequency` (fixed `1d`), `type` (`static`/`dynamic`), `symbols` array.
  - `Factors`: `selected_factors` [{name, params}], `preprocess` (zscore, missing_fill).
  - `Scoring`: `fusion_mode` (`linear`/`conditional`/`ai`), `linear.weights` (JSON), `conditional.rule`, `ai.model_path`, `scheduling` (frequency, rebalance_threshold), `constraints` (max_position_per_symbol).
  - `Execution`: `initial_cash`, `commission_rate`, `tax_rate`, `slippage_model`.
  - `Metadata`: `plan_id`, `name`, `created_at`, `description`, `save_path`.
- Defaults loaded from `data/plan_defaults.json` where present.

## Data Caches
- Symbols: `data/symbols_a.csv` (A-Shares + ETF) fetched via AkShare; used for UI suggestions and validation.
- Saved symbols: `data/saved_symbols.txt` persisted between sessions; drives UI symbol list.
- K-line cache: `data/kline/<code>.csv` created on download; normalized columns include `date`, `open`, `high`, `low`, `close`, optional `volume`.

## Factor Library
- CSV: `data/factor.csv` used to list available factors.
- JSON defaults: `data/factors/*.json` provide parameter templates per factor.
- Built-ins: `Do_Nothing`, `Buy_&_Hold` added if absent.

## Known Data Assumptions
- Daily frequency only; UI K-line uses AkShare daily endpoints.
- Universe symbols are raw codes matching AkShare expectations (e.g., `600519`).

