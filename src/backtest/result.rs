use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeEvent {
	pub index: usize,
	pub date: String,
	pub price: f64,
	pub side: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DrawdownSpan {
	pub peak_index: usize,
	pub trough_index: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
	pub initial_capital: f64,
	pub final_equity: f64,
	pub total_return_pct: f64,
	pub max_drawdown_pct: f64,
	pub trades: usize,
	#[serde(default)]
	pub equity_curve: Vec<f64>,
	#[serde(default)]
	pub dates: Vec<String>,
	#[serde(default)]
	pub close_prices: Vec<f64>,
	#[serde(default)]
	pub high_prices: Vec<f64>,
	#[serde(default)]
	pub low_prices: Vec<f64>,
	#[serde(default)]
	pub trade_events: Vec<TradeEvent>,
	#[serde(default)]
	pub max_drawdown_span: DrawdownSpan,
}
