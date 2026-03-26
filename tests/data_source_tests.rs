use beruto::data::data_source::load_daily_quotes;

#[test]
fn old_daily_csv_without_noon_close_uses_close_as_fallback() {
	let quotes = load_daily_quotes("data/159581_daily.csv")
		.expect("failed to load data/159581_daily.csv for noon_close fallback test");

	assert!(!quotes.is_empty(), "quotes should not be empty");

	for quote in &quotes {
		assert!(quote.noon_close > 0.0, "noon_close should be positive");
		assert_eq!(
			quote.noon_close, quote.close,
			"when noon_close column is missing, fallback should use close"
		);
	}
}
