pub mod base;
pub mod contrarian;
pub mod kdj;

use crate::strategy::base::Strategy;
use crate::strategy::contrarian::{BuyAndHoldStrategy, ContrarianStrategy, NoopStrategy};
use crate::strategy::kdj::KdjStrategy;

#[derive(Debug, Clone)]
pub struct StrategyParamSpec {
	pub name: &'static str,
	pub description: &'static str,
	pub default_value: Option<&'static str>,
}

#[derive(Debug, Clone)]
pub struct StrategySpec {
	pub id: &'static str,
	pub name: &'static str,
	pub description: &'static str,
	pub params: &'static [StrategyParamSpec],
	pub usage: &'static str,
}

const EMPTY_PARAMS: [StrategyParamSpec; 0] = [];

const CONTRARIAN_PARAMS: [StrategyParamSpec; 2] = [
	StrategyParamSpec {
		name: "buy-drop",
		description: "Buy trigger daily change threshold (<=, percent).",
		default_value: Some("-1.0"),
	},
	StrategyParamSpec {
		name: "sell-rise",
		description: "Sell trigger daily change threshold (>=, percent).",
		default_value: Some("1.0"),
	},
];

const KDJ_PARAMS: [StrategyParamSpec; 3] = [
	StrategyParamSpec {
		name: "period",
		description: "Lookback window used to compute the stochastic range.",
		default_value: Some("9"),
	},
	StrategyParamSpec {
		name: "buy-threshold",
		description: "Buy when J is at or below this level.",
		default_value: Some("20.0"),
	},
	StrategyParamSpec {
		name: "sell-threshold",
		description: "Sell when J is at or above this level.",
		default_value: Some("80.0"),
	},
];

const STRATEGY_SPECS: [StrategySpec; 4] = [
	StrategySpec {
		id: "noop",
		name: "No-op",
		description: "Never place orders and always hold.",
		params: &EMPTY_PARAMS,
		usage: "backtest --symbol 159581 --strategy noop",
	},
	StrategySpec {
		id: "buyhold",
		name: "Buy and Hold",
		description: "Buy at first bar and hold position.",
		params: &EMPTY_PARAMS,
		usage: "backtest --symbol 159581 --strategy buyhold",
	},
	StrategySpec {
		id: "contrarian",
		name: "Contrarian Simple",
		description: "Buy after drop threshold and sell after rise threshold.",
		params: &CONTRARIAN_PARAMS,
		usage: "backtest --symbol 159581 --strategy contrarian --buy-drop -1.0 --sell-rise 1.0",
	},
	StrategySpec {
		id: "kdj",
		name: "KDJ",
		description: "Use the KDJ oscillator and trade on J-line oversold/overbought levels.",
		params: &KDJ_PARAMS,
		usage: "backtest --symbol 159581 --strategy kdj --kdj-period 9 --kdj-buy-threshold 20.0 --kdj-sell-threshold 80.0",
	},
];

#[derive(Debug, Clone)]
pub enum StrategyConfig {
	Noop,
	BuyAndHold,
	Contrarian {
		buy_drop_threshold_pct: f64,
		sell_rise_threshold_pct: f64,
	},
	Kdj {
		period: usize,
		buy_threshold: f64,
		sell_threshold: f64,
	},
}

impl StrategyConfig {
	pub fn id(&self) -> &'static str {
		match self {
			Self::Noop => "noop",
			Self::BuyAndHold => "buyhold",
			Self::Contrarian { .. } => "contrarian",
			Self::Kdj { .. } => "kdj",
		}
	}
}

pub fn strategy_specs() -> &'static [StrategySpec] {
	&STRATEGY_SPECS
}

pub fn find_strategy_spec(id: &str) -> Option<&'static StrategySpec> {
	strategy_specs().iter().find(|spec| spec.id == id)
}

pub fn build_strategy(config: &StrategyConfig) -> Box<dyn Strategy> {
	match config {
		StrategyConfig::Noop => Box::new(NoopStrategy::new()),
		StrategyConfig::BuyAndHold => Box::new(BuyAndHoldStrategy::new()),
		StrategyConfig::Contrarian {
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		} => Box::new(ContrarianStrategy::with_thresholds(
			*buy_drop_threshold_pct,
			*sell_rise_threshold_pct,
		)),
		StrategyConfig::Kdj {
			period,
			buy_threshold,
			sell_threshold,
		} => Box::new(KdjStrategy::with_params(
			*period,
			*buy_threshold,
			*sell_threshold,
		)),
	}
}
