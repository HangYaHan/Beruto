# Manager Fixtures

This folder contains manager fixtures and test cases.

Implemented today:
- `void_baseline.json`: no-op baseline manager.
- `score_rank_descending.json`: score-ranked manager that orders intents by score.

Planned fixtures:
- `naive_dca_daily.json`: fixed periodic buy-only manager.
- `naive_equal_weight_rebalance.json`: simple equal-weight rebalance manager.

The planned fixtures document future semantics and are kept here so the folder can grow with the manager layer without changing the test layout.
