# Portfolio + Manager Evolution Plan (Critical Version)

## 0. Executive Verdict

1. Do **not** start with ML manager now.
2. First build a deterministic, rules-based manager on top of portfolio semantics.
3. Only proceed to ML after strict out-of-sample validation is consistently positive.

Reason:
- Without strict evaluation, ML will mostly amplify overfitting.
- Current architecture is single-symbol and strategy-driven, so direct ML introduces a large and risky coupling change.

---

## 1. Problem Reframe

Current engine answers: "How did one strategy behave on one symbol?"

Target engine should answer:
"Given a universe, multiple candidate strategies, capital/risk constraints, and realistic costs, what action allocation should be executed now?"

This is a decision problem under:
- non-stationary environment,
- delayed rewards,
- transaction frictions,
- model uncertainty.

So the goal is **robustness**, not in-sample maximum.

---

## 2. Quantify The Manager (State / Action / Reward)

### 2.1 State `s_t`

At minimum:
- Market features per symbol: return windows, realized volatility, drawdown, liquidity proxies.
- Strategy health per (symbol, strategy): recent hit-rate, payoff ratio, turnover, rolling drawdown.
- Portfolio state: current weights, cash, gross/net exposure, risk budget usage.

### 2.2 Action `a_t`

Start with discrete action space:
- enable/disable a strategy on a symbol,
- choose small finite position buckets (0%, 25%, 50%, 100% of per-symbol cap).

This keeps exploration tractable and easier to debug.

### 2.3 Reward `r_t`

Use friction-aware, risk-penalized reward instead of pure pnl:

$$
r_t = \Delta V_t - \lambda_1\,TC_t - \lambda_2\,DD_t - \lambda_3\,Turnover_t
$$

where:
- $\Delta V_t$: equity change,
- $TC_t$: costs (fee + slippage),
- $DD_t$: drawdown penalty,
- $Turnover_t$: trading intensity penalty.

Model selection objective should include stability:

$$
J = \text{Sharpe}_{OOS} - \alpha\,\sigma(\text{Sharpe}_{folds})
$$

Interpretation: prefer slightly lower mean performance with lower fold variance.

---

## 3. Convergence vs Brute Force

### 3.1 Brute Force

Not realistic once dimensions are combined:
- symbols × strategies × thresholds × position buckets × rebalance timings.

Search space grows exponentially.

### 3.2 Convergence

In financial control, expecting global optimum convergence is usually the wrong target.

Practical target:
- statistically stable improvement,
- controlled degradation in unseen regimes,
- low sensitivity to small hyper-parameter changes.

---

## 4. Is The Result Meaningful?

This concern is correct and must be treated as a hard gate.

Required validation stack before any ML claim:

1. Walk-forward train/validation/test.
2. Leakage control (purged / embargo split idea).
3. Deflated Sharpe Ratio.
4. Probability of Backtest Overfitting (PBO).
5. White's Reality Check or SPA for multiple comparisons.

If these are not passing, "best backtest" is likely noise.

---

## 5. Refactor Scope Estimation

Expected impact: medium to large.

Likely touched areas:
- backtest engine event loop (single symbol -> multi-symbol timeline).
- strategy interface (signal-only -> candidate intents + metadata).
- result model (single curve -> portfolio curve + per-symbol attribution).
- CLI contract (`backtest` + `run` should support universe and manager mode).

Rough estimate:
- 40% to 60% of core backtest flow will be touched,
- most strategy internals can stay reusable if wrapped correctly.

---

## 6. Recommended Build Order (Minimal Runnable First)

1. Add portfolio accounting and risk constraints (no ML).
2. Add deterministic manager with explicit rules (enable/disable + weight cap).
3. Add robust evaluation pipeline (walk-forward + overfit diagnostics).
4. Add contextual bandit style manager.
5. Consider full RL only if step 4 is demonstrably stable.

Stop condition:
- If rules-based manager cannot improve robustly out-of-sample, do not proceed to ML.

---

## 7. Rust Declarations (Manager + Portfolio)

These declarations are intentionally minimal and compatible with gradual migration.

```rust
use std::collections::HashMap;

use crate::data::data_source::DailyQuote;

pub type Symbol = String;
pub type StrategyId = String;

#[derive(Debug, Clone)]
pub struct SignalIntent {
    pub symbol: Symbol,
    pub strategy_id: StrategyId,
    pub score: f64,             // confidence or ranking score
    pub target_weight: f64,     // suggested weight in [0, 1]
}

#[derive(Debug, Clone)]
pub struct SymbolSnapshot {
    pub symbol: Symbol,
    pub quote: DailyQuote,
}

#[derive(Debug, Clone)]
pub struct Position {
    pub symbol: Symbol,
    pub shares: f64,
    pub avg_cost: f64,
    pub last_price: f64,
}

#[derive(Debug, Clone)]
pub struct PortfolioConfig {
    pub max_symbol_weight: f64, // e.g. 0.2
    pub max_turnover: f64,      // per rebalance step
    pub fee_bps: f64,
    pub slippage_bps: f64,
}

#[derive(Debug, Clone)]
pub struct Portfolio {
    pub cash: f64,
    pub positions: HashMap<Symbol, Position>,
    pub config: PortfolioConfig,
}

#[derive(Debug, Clone)]
pub struct RiskReport {
    pub gross_exposure: f64,
    pub net_exposure: f64,
    pub turnover: f64,
    pub max_symbol_weight_now: f64,
}

#[derive(Debug, Clone)]
pub enum OrderSide {
    Buy,
    Sell,
}

#[derive(Debug, Clone)]
pub struct OrderDecision {
    pub symbol: Symbol,
    pub side: OrderSide,
    pub quantity: f64,
    pub reason: String,
}

#[derive(Debug, Clone)]
pub struct ManagerContext {
    pub t_index: usize,
    pub snapshots: Vec<SymbolSnapshot>,
    pub candidate_intents: Vec<SignalIntent>,
    pub portfolio: Portfolio,
}

pub trait Manager {
    fn name(&self) -> &str;

    // Decide what to execute now (including reject/accept logic).
    fn decide(&mut self, ctx: &ManagerContext) -> Vec<OrderDecision>;

    // Optional online update hook for future ML manager.
    fn on_step_end(&mut self, _reward: f64, _next_ctx: &ManagerContext) {}
}

impl Portfolio {
    pub fn equity(&self) -> f64 {
        let positions_value: f64 = self
            .positions
            .values()
            .map(|p| p.shares * p.last_price)
            .sum();
        self.cash + positions_value
    }

    pub fn risk_report(&self) -> RiskReport {
        let equity = self.equity().max(1e-12);
        let gross: f64 = self
            .positions
            .values()
            .map(|p| (p.shares * p.last_price).abs())
            .sum();
        let net: f64 = self
            .positions
            .values()
            .map(|p| p.shares * p.last_price)
            .sum();
        let max_symbol = self
            .positions
            .values()
            .map(|p| (p.shares * p.last_price).abs() / equity)
            .fold(0.0_f64, f64::max);

        RiskReport {
            gross_exposure: gross / equity,
            net_exposure: net / equity,
            turnover: 0.0, // filled by execution layer each step
            max_symbol_weight_now: max_symbol,
        }
    }
}
```

Notes:
- Keep `Manager` as pure decision logic; execution and fills remain in backtest/broker layer.
- `SignalIntent` allows reusing existing strategies by wrapping current `Signal` output.
- `on_step_end` is the future bridge to online learning without forcing ML now.

---

## 8. Suggested File Placement

When implementing, you can split as:
- `src/portfolio/mod.rs` for `Portfolio`, `Position`, risk/accounting.
- `src/manager/mod.rs` for `Manager` trait and rule-based manager.
- `src/backtest/engine.rs` updated to call manager each step.

This keeps migration incremental and testable.

---

## 9. References To Read First

1. Bailey et al. (2014), *The Probability of Backtest Overfitting*.
2. Bailey & Lopez de Prado (2014), *The Deflated Sharpe Ratio*.
3. White (2000), *A Reality Check for Data Snooping*.
4. Hansen (2005), *A Test for Superior Predictive Ability*.
5. Gu, Kelly, Xiu (2020), *Empirical Asset Pricing via Machine Learning*.
6. Garleanu & Pedersen (2013), *Dynamic Trading with Predictable Returns and Transaction Costs*.
7. Cover (1991), *Universal Portfolios*.

---

## 10. Practical Guardrail

If you cannot produce stable out-of-sample gains with deterministic manager + strict evaluation,
do not escalate to ML.

That is not a tooling limitation; it is signal quality reality.
