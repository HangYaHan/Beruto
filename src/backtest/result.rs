#[derive(Debug)]
pub struct BacktestResult {
	pub initial_capital: f64,
	pub final_equity: f64,
	pub total_return_pct: f64,
	pub max_drawdown_pct: f64,
	pub trades: usize,
	pub equity_curve: Vec<f64>,
}
