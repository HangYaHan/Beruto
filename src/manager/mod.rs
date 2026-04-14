use crate::data::data_source::DailyQuote;
use crate::portfolio::Portfolio;
use serde::{Deserialize, Serialize};

pub type Symbol = String;
pub type StrategyId = String;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub enum ManagerKind {
    Void,
    ScoreRank,
}

impl Default for ManagerKind {
    fn default() -> Self {
        Self::Void
    }
}

#[derive(Debug, Clone)]
pub struct SignalIntent {
    pub symbol: Symbol,
    pub strategy_id: StrategyId,
    pub score: f64,
    pub target_weight: f64,
}

#[derive(Debug, Clone)]
pub struct SymbolSnapshot {
    pub symbol: Symbol,
    pub quote: DailyQuote,
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
    fn decide(&mut self, ctx: &ManagerContext) -> Vec<OrderDecision>;
}

#[derive(Debug, Default)]
pub struct VoidManager;

impl Manager for VoidManager {
    fn name(&self) -> &str {
        "VoidManager"
    }

    fn decide(&mut self, _ctx: &ManagerContext) -> Vec<OrderDecision> {
        Vec::new()
    }
}

#[derive(Debug, Default)]
pub struct ScoreRankManager;

impl Manager for ScoreRankManager {
    fn name(&self) -> &str {
        "ScoreRankManager"
    }

    fn decide(&mut self, ctx: &ManagerContext) -> Vec<OrderDecision> {
        let mut intents = ctx.candidate_intents.clone();
        intents.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));

        intents
            .into_iter()
            .map(|intent| OrderDecision {
                symbol: intent.symbol,
                side: if intent.target_weight > 0.0 {
                    OrderSide::Buy
                } else {
                    OrderSide::Sell
                },
                quantity: intent.target_weight.abs(),
                reason: format!("ranked by score={} strategy={}", intent.score, intent.strategy_id),
            })
            .collect()
    }
}
