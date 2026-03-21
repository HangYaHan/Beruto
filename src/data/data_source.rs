use serde::Deserialize;
use std::error::Error;
use std::fs::File;
use std::path::Path;

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct DailyQuote {
	pub date: String,
	pub open: f64,
	pub close: f64,
	pub high: f64,
	pub low: f64,
	pub volume: f64,
	pub amount: f64,
	pub amplitude_pct: f64,
}

pub fn load_daily_quotes<P: AsRef<Path>>(file_path: P) -> Result<Vec<DailyQuote>, Box<dyn Error>> {
	let file = File::open(file_path)?;
	let mut reader = csv::Reader::from_reader(file);
	let mut quotes = Vec::new();

	for row in reader.deserialize() {
		let quote: DailyQuote = row?;
		quotes.push(quote);
	}

	Ok(quotes)
}
