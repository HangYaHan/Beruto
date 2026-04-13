use crate::backtest::result::{BacktestResult, DrawdownSpan, TradeEvent};
use crate::data::data_source::DailyQuote;
use crate::strategy::base::{Signal, Strategy};

fn compute_max_drawdown(equity_curve: &[f64]) -> (f64, DrawdownSpan) {
	if equity_curve.is_empty() {
		return (0.0, DrawdownSpan::default());
	}

	let mut peak = equity_curve[0];
	let mut peak_index = 0usize;
	let mut max_drawdown = 0.0;
	let mut max_span = DrawdownSpan::default();

	for (index, &equity) in equity_curve.iter().enumerate() {
		if equity > peak {
			peak = equity;
			peak_index = index;
		}

		let drawdown = (peak - equity) / peak;
		if drawdown > max_drawdown {
			max_drawdown = drawdown;
			max_span = DrawdownSpan {
				peak_index,
				trough_index: index,
			};
		}
	}

	(max_drawdown * 100.0, max_span)
}

pub fn run_backtest<S: Strategy + ?Sized>(
	strategy: &mut S,
	quotes: &[DailyQuote],
	initial_capital: f64,
) -> BacktestResult {
	let mut cash = initial_capital;
	let mut shares = 0.0_f64;
	let mut trades = 0usize;
	let mut equity_curve = Vec::with_capacity(quotes.len());
	let mut dates = Vec::with_capacity(quotes.len());
	let mut close_prices = Vec::with_capacity(quotes.len());
	let mut high_prices = Vec::with_capacity(quotes.len());
	let mut low_prices = Vec::with_capacity(quotes.len());
	let mut trade_events = Vec::new();

	for (index, quote) in quotes.iter().enumerate() {
		match strategy.on_bar(quote) {
			Signal::Buy if shares == 0.0 => {
				shares = cash / quote.close;
				cash = 0.0;
				trades += 1;
				trade_events.push(TradeEvent {
					index,
					date: quote.date.clone(),
					price: quote.close,
					side: "buy".to_string(),
				});
			}
			Signal::Sell if shares > 0.0 => {
				cash = shares * quote.close;
				shares = 0.0;
				trades += 1;
				trade_events.push(TradeEvent {
					index,
					date: quote.date.clone(),
					price: quote.close,
					side: "sell".to_string(),
				});
			}
			_ => {}
		}

		dates.push(quote.date.clone());
		close_prices.push(quote.close);
		high_prices.push(quote.high);
		low_prices.push(quote.low);

		let equity = cash + shares * quote.close;
		equity_curve.push(equity);
	}

	let final_equity = equity_curve.last().copied().unwrap_or(initial_capital);
	let total_return_pct = (final_equity / initial_capital - 1.0) * 100.0;
	let (max_drawdown_pct, max_drawdown_span) = compute_max_drawdown(&equity_curve);

	BacktestResult {
		initial_capital,
		final_equity,
		total_return_pct,
		max_drawdown_pct,
		trades,
		equity_curve,
		dates,
		close_prices,
		high_prices,
		low_prices,
		trade_events,
		max_drawdown_span,
	}
}
