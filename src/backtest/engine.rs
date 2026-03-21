use crate::backtest::result::BacktestResult;
use crate::data::data_source::DailyQuote;
use crate::strategy::base::{Signal, Strategy};

fn compute_max_drawdown_pct(equity_curve: &[f64]) -> f64 {
	if equity_curve.is_empty() {
		return 0.0;
	}

	let mut peak = equity_curve[0];
	let mut max_drawdown = 0.0;

	for &equity in equity_curve {
		if equity > peak {
			peak = equity;
		}

		let drawdown = (peak - equity) / peak;
		if drawdown > max_drawdown {
			max_drawdown = drawdown;
		}
	}

	max_drawdown * 100.0
}

pub fn run_backtest<S: Strategy>(
	strategy: &mut S,
	quotes: &[DailyQuote],
	initial_capital: f64,
) -> BacktestResult {
	let mut cash = initial_capital;
	let mut shares = 0.0_f64;
	let mut trades = 0usize;
	let mut equity_curve = Vec::with_capacity(quotes.len());

	for quote in quotes {
		match strategy.on_bar(quote) {
			Signal::Buy if shares == 0.0 => {
				shares = cash / quote.close;
				cash = 0.0;
				trades += 1;
			}
			Signal::Sell if shares > 0.0 => {
				cash = shares * quote.close;
				shares = 0.0;
				trades += 1;
			}
			_ => {}
		}

		let equity = cash + shares * quote.close;
		equity_curve.push(equity);
	}

	let final_equity = equity_curve.last().copied().unwrap_or(initial_capital);
	let total_return_pct = (final_equity / initial_capital - 1.0) * 100.0;
	let max_drawdown_pct = compute_max_drawdown_pct(&equity_curve);

	BacktestResult {
		initial_capital,
		final_equity,
		total_return_pct,
		max_drawdown_pct,
		trades,
		equity_curve,
	}
}
