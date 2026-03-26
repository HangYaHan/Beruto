pub mod base;
pub mod contrarian;

use crate::strategy::base::Strategy;
use crate::strategy::contrarian::{BuyAndHoldStrategy, ContrarianStrategy};

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

const STRATEGY_SPECS: [StrategySpec; 2] = [
	StrategySpec {
		id: "buyhold",
		name: "Buy and Hold",
		description: "Buy at first bar and hold position.",
		params: &EMPTY_PARAMS,
		usage: "run --symbol 159581 --strategy buyhold",
	},
	StrategySpec {
		id: "contrarian",
		name: "Contrarian Simple",
		description: "Buy after drop threshold and sell after rise threshold.",
		params: &CONTRARIAN_PARAMS,
		usage: "run --symbol 159581 --strategy contrarian --buy-drop -1.0 --sell-rise 1.0",
	},
];

#[derive(Debug, Clone)]
pub enum StrategyConfig {
	BuyAndHold,
	Contrarian {
		buy_drop_threshold_pct: f64,
		sell_rise_threshold_pct: f64,
	},
}

impl StrategyConfig {
	pub fn id(&self) -> &'static str {
		match self {
			Self::BuyAndHold => "buyhold",
			Self::Contrarian { .. } => "contrarian",
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
		StrategyConfig::BuyAndHold => Box::new(BuyAndHoldStrategy::new()),
		StrategyConfig::Contrarian {
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		} => Box::new(ContrarianStrategy::with_thresholds(
			*buy_drop_threshold_pct,
			*sell_rise_threshold_pct,
		)),
	}
}
