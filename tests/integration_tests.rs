use beruto::backtest::engine::run_backtest;
use beruto::data::data_source::load_daily_quotes;
use beruto::strategy::buy_and_hold::BuyAndHoldStrategy;
use beruto::strategy::contrarian::ContrarianStrategy;

#[test]
fn smoke_backtest_159581_csv() {
	let quotes = load_daily_quotes("data/159581_daily.csv")
		.expect("failed to load data/159581_daily.csv for integration test");

	assert!(!quotes.is_empty(), "quotes should not be empty");

	let mut strategy = BuyAndHoldStrategy::new();
	let result = run_backtest(&mut strategy, &quotes, 100_000.0);

	assert_eq!(result.equity_curve.len(), quotes.len());
	assert!(result.final_equity > 0.0);
	assert!(result.trades >= 1);
	assert!(result.max_drawdown_pct >= 0.0);
	assert!(result.max_drawdown_pct <= 100.0);
}

#[test]
fn smoke_backtest_159581_contrarian() {
	let quotes = load_daily_quotes("data/159581_daily.csv")
		.expect("failed to load data/159581_daily.csv for integration test");

	assert!(!quotes.is_empty(), "quotes should not be empty");

	let mut strategy = ContrarianStrategy::new();
	let result = run_backtest(&mut strategy, &quotes, 100_000.0);

	assert_eq!(result.equity_curve.len(), quotes.len());
	assert!(result.final_equity > 0.0);
	assert!(result.max_drawdown_pct >= 0.0);
	assert!(result.max_drawdown_pct <= 100.0);
}

#[test]
fn smoke_backtest_159581_contrarian_configurable_thresholds() {
	let quotes = load_daily_quotes("data/159581_daily.csv")
		.expect("failed to load data/159581_daily.csv for integration test");

	let mut strategy = ContrarianStrategy::with_thresholds(-0.5, 0.5);
	let result = run_backtest(&mut strategy, &quotes, 100_000.0);

	assert_eq!(result.equity_curve.len(), quotes.len());
	assert!(result.final_equity > 0.0);
	assert!(result.max_drawdown_pct >= 0.0);
	assert!(result.max_drawdown_pct <= 100.0);
}
