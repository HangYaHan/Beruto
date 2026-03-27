pub mod base;
pub mod buy_and_hold;
pub mod contrarian;
pub mod kdj;
pub mod macd;

use crate::strategy::base::Strategy;
use crate::strategy::buy_and_hold::BuyAndHoldStrategy;
use crate::strategy::contrarian::ContrarianStrategy;
use crate::strategy::kdj::KdjStrategy;
use crate::strategy::macd::MacdStrategy;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StrategyParamType {
    Float,
    Integer,
}

#[derive(Debug, Clone)]
pub struct StrategyParamSpec {
    pub name: &'static str,
    pub description: &'static str,
    pub default_value: Option<&'static str>,
    pub kind: StrategyParamType,
    pub min_value: Option<f64>,
    pub max_value: Option<f64>,
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
        kind: StrategyParamType::Float,
        min_value: Some(-100.0),
        max_value: Some(100.0),
    },
    StrategyParamSpec {
        name: "sell-rise",
        description: "Sell trigger daily change threshold (>=, percent).",
        default_value: Some("1.0"),
        kind: StrategyParamType::Float,
        min_value: Some(-100.0),
        max_value: Some(100.0),
    },
];

const MACD_PARAMS: [StrategyParamSpec; 3] = [
    StrategyParamSpec {
        name: "fast-period",
        description: "Fast EMA period.",
        default_value: Some("12"),
        kind: StrategyParamType::Integer,
        min_value: Some(1.0),
        max_value: Some(500.0),
    },
    StrategyParamSpec {
        name: "slow-period",
        description: "Slow EMA period.",
        default_value: Some("26"),
        kind: StrategyParamType::Integer,
        min_value: Some(2.0),
        max_value: Some(1000.0),
    },
    StrategyParamSpec {
        name: "signal-period",
        description: "Signal EMA period.",
        default_value: Some("9"),
        kind: StrategyParamType::Integer,
        min_value: Some(1.0),
        max_value: Some(500.0),
    },
];

const KDJ_PARAMS: [StrategyParamSpec; 1] = [StrategyParamSpec {
    name: "period",
    description: "Rolling window period for RSV.",
    default_value: Some("9"),
    kind: StrategyParamType::Integer,
    min_value: Some(2.0),
    max_value: Some(500.0),
}];

const STRATEGY_SPECS: [StrategySpec; 4] = [
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
    StrategySpec {
        id: "macd",
        name: "MACD Crossover",
        description: "Buy on DIF/DEA golden cross, sell on dead cross.",
        params: &MACD_PARAMS,
        usage: "run --symbol 159581 --strategy macd --fast-period 12 --slow-period 26 --signal-period 9",
    },
    StrategySpec {
        id: "kdj",
        name: "KDJ Crossover",
        description: "Buy on K crossing above D, sell on crossing below.",
        params: &KDJ_PARAMS,
        usage: "run --symbol 159581 --strategy kdj --period 9",
    },
];

#[derive(Debug, Clone)]
pub enum StrategyConfig {
    BuyAndHold,
    Contrarian {
        buy_drop_threshold_pct: f64,
        sell_rise_threshold_pct: f64,
    },
    Macd {
        fast_period: u32,
        slow_period: u32,
        signal_period: u32,
    },
    Kdj {
        period: usize,
    },
}

impl StrategyConfig {
    pub fn id(&self) -> &'static str {
        match self {
            Self::BuyAndHold => "buyhold",
            Self::Contrarian { .. } => "contrarian",
            Self::Macd { .. } => "macd",
            Self::Kdj { .. } => "kdj",
        }
    }
}

fn parse_default(param: &StrategyParamSpec) -> f64 {
    param
        .default_value
        .and_then(|raw| raw.parse::<f64>().ok())
        .unwrap_or(0.0)
}

pub fn default_strategy_param_values(strategy_id: &str) -> HashMap<String, f64> {
    let mut values = HashMap::new();
    if let Some(spec) = find_strategy_spec(strategy_id) {
        for param in spec.params {
            values.insert(param.name.to_string(), parse_default(param));
        }
    }
    values
}

pub fn validate_strategy_param(strategy_id: &str, name: &str, value: f64) -> Result<(), String> {
    let spec = find_strategy_spec(strategy_id)
        .ok_or_else(|| format!("Unknown strategy: {strategy_id}"))?;
    let param = spec
        .params
        .iter()
        .find(|p| p.name == name)
        .ok_or_else(|| format!("Unknown parameter '{name}' for strategy '{strategy_id}'"))?;

    if let Some(min) = param.min_value {
        if value < min {
            return Err(format!("{name} must be >= {min}"));
        }
    }
    if let Some(max) = param.max_value {
        if value > max {
            return Err(format!("{name} must be <= {max}"));
        }
    }
    if param.kind == StrategyParamType::Integer && value.fract() != 0.0 {
        return Err(format!("{name} must be an integer"));
    }

    Ok(())
}

pub fn strategy_config_from_values(
    strategy_id: &str,
    values: &HashMap<String, f64>,
) -> Result<StrategyConfig, String> {
    let defaulted = |name: &str| -> f64 {
        values.get(name).copied().unwrap_or_else(|| {
            default_strategy_param_values(strategy_id)
                .get(name)
                .copied()
                .unwrap_or(0.0)
        })
    };

    let config = match strategy_id {
        "buyhold" => StrategyConfig::BuyAndHold,
        "contrarian" => {
            let buy_drop_threshold_pct = defaulted("buy-drop");
            let sell_rise_threshold_pct = defaulted("sell-rise");
            validate_strategy_param("contrarian", "buy-drop", buy_drop_threshold_pct)?;
            validate_strategy_param("contrarian", "sell-rise", sell_rise_threshold_pct)?;
            StrategyConfig::Contrarian {
                buy_drop_threshold_pct,
                sell_rise_threshold_pct,
            }
        }
        "macd" => {
            let fast_period = defaulted("fast-period");
            let slow_period = defaulted("slow-period");
            let signal_period = defaulted("signal-period");
            validate_strategy_param("macd", "fast-period", fast_period)?;
            validate_strategy_param("macd", "slow-period", slow_period)?;
            validate_strategy_param("macd", "signal-period", signal_period)?;

            if fast_period >= slow_period {
                return Err("fast-period must be smaller than slow-period".to_string());
            }

            StrategyConfig::Macd {
                fast_period: fast_period as u32,
                slow_period: slow_period as u32,
                signal_period: signal_period as u32,
            }
        }
        "kdj" => {
            let period = defaulted("period");
            validate_strategy_param("kdj", "period", period)?;
            StrategyConfig::Kdj {
                period: period as usize,
            }
        }
        _ => return Err(format!("Unknown strategy: {strategy_id}")),
    };

    Ok(config)
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
        StrategyConfig::Macd {
            fast_period,
            slow_period,
            signal_period,
        } => Box::new(MacdStrategy::with_periods(
            *fast_period as f64,
            *slow_period as f64,
            *signal_period as f64,
        )),
        StrategyConfig::Kdj { period } => Box::new(KdjStrategy::with_period(*period)),
    }
}
