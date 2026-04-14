use std::collections::HashMap;

pub type Symbol = String;

#[derive(Debug, Clone)]
pub struct Position {
    pub symbol: Symbol,
    pub shares: f64,
    pub avg_cost: f64,
    pub last_price: f64,
}

#[derive(Debug, Clone)]
pub struct PortfolioConfig {
    pub max_symbol_weight: f64,
    pub max_turnover: f64,
}

impl Default for PortfolioConfig {
    fn default() -> Self {
        Self {
            max_symbol_weight: 1.0,
            max_turnover: 1.0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Portfolio {
    pub cash: f64,
    pub positions: HashMap<Symbol, Position>,
    pub config: PortfolioConfig,
}

impl Portfolio {
    pub fn new(initial_cash: f64, config: PortfolioConfig) -> Self {
        Self {
            cash: initial_cash,
            positions: HashMap::new(),
            config,
        }
    }

    pub fn equity(&self) -> f64 {
        let positions_value: f64 = self
            .positions
            .values()
            .map(|p| p.shares * p.last_price)
            .sum();
        self.cash + positions_value
    }

    pub fn gross_exposure(&self) -> f64 {
        self.positions
            .values()
            .map(|p| (p.shares * p.last_price).abs())
            .sum()
    }
}
