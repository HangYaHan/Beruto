use crate::backtest::result::{BacktestResult, DrawdownSpan, TradeEvent};
use crate::data::data_source::DailyQuote;
use crate::data::settings::{load_settings, AccountProfile, AssetClass, DividendTaxRule, FeeRule};
use crate::strategy::base::{Signal, Strategy};

#[derive(Debug, Clone)]
struct FeeBreakdown {
	commission: f64,
	transaction_tax: f64,
	transfer_fee: f64,
}

impl FeeBreakdown {
	fn total(&self) -> f64 {
		self.commission + self.transaction_tax + self.transfer_fee
	}
}

#[derive(Debug, Clone)]
struct CostModel {
	fee_rule: FeeRule,
	dividend_tax_rule: DividendTaxRule,
}

fn compute_fee(amount: f64, fee_rule: &FeeRule, is_sell: bool) -> FeeBreakdown {
	if amount <= 0.0 {
		return FeeBreakdown {
			commission: 0.0,
			transaction_tax: 0.0,
			transfer_fee: 0.0,
		};
	}

	let commission = (amount * fee_rule.commission_rate).max(fee_rule.commission_min);
	let transfer_fee = amount * fee_rule.transfer_rate;
	let transaction_tax = if is_sell {
		amount * fee_rule.transaction_tax_rate
	} else {
		0.0
	};

	FeeBreakdown {
		commission,
		transaction_tax,
		transfer_fee,
	}
}

fn resolve_dividend_tax_rate(rule: &DividendTaxRule, holding_days: u32) -> f64 {
	for bracket in &rule.brackets {
		if holding_days < bracket.min_holding_days {
			continue;
		}
		match bracket.max_holding_days {
			Some(max) if holding_days > max => continue,
			_ => return bracket.tax_rate,
		}
	}
	0.0
}

fn cost_model_from_symbol(symbol: &str) -> CostModel {
	if let Ok(settings) = load_settings() {
		let profile: &AccountProfile = &settings.account_profile;
		let class = settings.resolve_asset_class(symbol).unwrap_or(AssetClass::Stock);
		match class {
			AssetClass::Stock => CostModel {
				fee_rule: profile.stock_fee.clone(),
				dividend_tax_rule: profile.stock_dividend_tax.clone(),
			},
			AssetClass::Etf => CostModel {
				fee_rule: profile.etf_fee.clone(),
				dividend_tax_rule: profile.etf_dividend_tax.clone(),
			},
		}
	} else {
		CostModel {
			fee_rule: FeeRule::default(),
			dividend_tax_rule: DividendTaxRule::default(),
		}
	}
}

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

pub fn run_backtest_for_symbol<S: Strategy + ?Sized>(
	strategy: &mut S,
	symbol: &str,
	quotes: &[DailyQuote],
	initial_capital: f64,
) -> BacktestResult {
	let cost_model = cost_model_from_symbol(symbol);
	run_backtest_with_cost_model(strategy, quotes, initial_capital, &cost_model)
}

fn run_backtest_with_cost_model<S: Strategy + ?Sized>(
	strategy: &mut S,
	quotes: &[DailyQuote],
	initial_capital: f64,
	cost_model: &CostModel,
) -> BacktestResult {
	let mut cash = initial_capital;
	let mut gross_cash = initial_capital;
	let mut shares = 0.0_f64;
	let mut trades = 0usize;
	let mut equity_curve = Vec::with_capacity(quotes.len());
	let mut gross_equity_curve = Vec::with_capacity(quotes.len());
	let mut dates = Vec::with_capacity(quotes.len());
	let mut close_prices = Vec::with_capacity(quotes.len());
	let mut high_prices = Vec::with_capacity(quotes.len());
	let mut low_prices = Vec::with_capacity(quotes.len());
	let mut trade_events = Vec::new();
	let mut commission_total = 0.0;
	let mut transaction_tax_total = 0.0;
	let mut transfer_fee_total = 0.0;
	let mut dividend_income_total = 0.0;
	let mut dividend_tax_total = 0.0;
	let mut position_entry_index: Option<usize> = None;

	for (index, quote) in quotes.iter().enumerate() {
		if shares > 0.0 && quote.dividend_per_share > 0.0 {
			let dividend_income = shares * quote.dividend_per_share;
			let holding_days = position_entry_index
				.map(|entry| index.saturating_sub(entry) as u32)
				.unwrap_or(0);
			let dividend_tax_rate =
				resolve_dividend_tax_rate(&cost_model.dividend_tax_rule, holding_days);
			let dividend_tax = dividend_income * dividend_tax_rate;

			cash += dividend_income - dividend_tax;
			gross_cash += dividend_income;
			dividend_income_total += dividend_income;
			dividend_tax_total += dividend_tax;

			trade_events.push(TradeEvent {
				index,
				date: quote.date.clone(),
				price: quote.close,
				side: "dividend".to_string(),
				commission: 0.0,
				transaction_tax: 0.0,
				transfer_fee: 0.0,
				dividend_income,
				dividend_tax,
			});
		}

		match strategy.on_bar(quote) {
			Signal::Buy if shares == 0.0 => {
				let mut trade_amount = cash;
				for _ in 0..2 {
					let fee = compute_fee(trade_amount, &cost_model.fee_rule, false);
					trade_amount = (cash - fee.total()).max(0.0);
				}

				let fee = compute_fee(trade_amount, &cost_model.fee_rule, false);
				shares = if quote.close > 0.0 {
					trade_amount / quote.close
				} else {
					0.0
				};
				cash -= trade_amount + fee.total();
				gross_cash -= trade_amount;
				if cash < 0.0 {
					cash = 0.0;
				}

				commission_total += fee.commission;
				transaction_tax_total += fee.transaction_tax;
				transfer_fee_total += fee.transfer_fee;
				trades += 1;
				position_entry_index = Some(index);
				trade_events.push(TradeEvent {
					index,
					date: quote.date.clone(),
					price: quote.close,
					side: "buy".to_string(),
					commission: fee.commission,
					transaction_tax: fee.transaction_tax,
					transfer_fee: fee.transfer_fee,
					dividend_income: 0.0,
					dividend_tax: 0.0,
				});
			}
			Signal::Sell if shares > 0.0 => {
				let trade_amount = shares * quote.close;
				let fee = compute_fee(trade_amount, &cost_model.fee_rule, true);
				cash += trade_amount - fee.total();
				gross_cash += trade_amount;

				commission_total += fee.commission;
				transaction_tax_total += fee.transaction_tax;
				transfer_fee_total += fee.transfer_fee;
				shares = 0.0;
				trades += 1;
				position_entry_index = None;
				trade_events.push(TradeEvent {
					index,
					date: quote.date.clone(),
					price: quote.close,
					side: "sell".to_string(),
					commission: fee.commission,
					transaction_tax: fee.transaction_tax,
					transfer_fee: fee.transfer_fee,
					dividend_income: 0.0,
					dividend_tax: 0.0,
				});
			}
			_ => {}
		}

		dates.push(quote.date.clone());
		close_prices.push(quote.close);
		high_prices.push(quote.high);
		low_prices.push(quote.low);

		let equity = cash + shares * quote.close;
		let gross_equity = gross_cash + shares * quote.close;
		equity_curve.push(equity);
		gross_equity_curve.push(gross_equity);
	}

	let final_equity = equity_curve.last().copied().unwrap_or(initial_capital);
	let gross_final_equity = gross_equity_curve
		.last()
		.copied()
		.unwrap_or(initial_capital);
	let gross_return_pct = (gross_final_equity / initial_capital - 1.0) * 100.0;
	let net_return_pct = (final_equity / initial_capital - 1.0) * 100.0;
	let total_return_pct = net_return_pct;
	let (max_drawdown_pct, max_drawdown_span) = compute_max_drawdown(&equity_curve);
	let tax_fee_total = commission_total + transaction_tax_total + transfer_fee_total + dividend_tax_total;
	let dividend_yield_pct = (dividend_income_total / initial_capital) * 100.0;

	BacktestResult {
		initial_capital,
		final_equity,
		gross_final_equity,
		total_return_pct,
		gross_return_pct,
		net_return_pct,
		max_drawdown_pct,
		trades,
		commission_total,
		transaction_tax_total,
		transfer_fee_total,
		tax_fee_total,
		dividend_income_total,
		dividend_tax_total,
		dividend_yield_pct,
		equity_curve,
		dates,
		close_prices,
		high_prices,
		low_prices,
		trade_events,
		max_drawdown_span,
	}
}
