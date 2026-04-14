use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeEvent {
	pub index: usize,
	pub date: String,
	pub price: f64,
	pub side: String,
	#[serde(default)]
	pub commission: f64,
	#[serde(default)]
	pub transaction_tax: f64,
	#[serde(default)]
	pub transfer_fee: f64,
	#[serde(default)]
	pub dividend_income: f64,
	#[serde(default)]
	pub dividend_tax: f64,
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
	#[serde(default)]
	pub gross_final_equity: f64,
	pub total_return_pct: f64,
	#[serde(default)]
	pub gross_return_pct: f64,
	#[serde(default)]
	pub net_return_pct: f64,
	pub max_drawdown_pct: f64,
	pub trades: usize,
	#[serde(default)]
	pub commission_total: f64,
	#[serde(default)]
	pub transaction_tax_total: f64,
	#[serde(default)]
	pub transfer_fee_total: f64,
	#[serde(default)]
	pub tax_fee_total: f64,
	#[serde(default)]
	pub dividend_income_total: f64,
	#[serde(default)]
	pub dividend_tax_total: f64,
	#[serde(default)]
	pub dividend_yield_pct: f64,
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
