use std::error::Error;
use std::fs::File;
use std::io::{Error as IoError, ErrorKind};
use std::path::Path;

use crate::data::fetcher::fetch_and_store_daily_quotes;

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct DailyQuote {
	pub date: String,
	pub open: f64,
	pub noon_close: f64,
	pub close: f64,
	pub dividend_per_share: f64,
	pub high: f64,
	pub low: f64,
	pub volume: f64,
	pub amount: f64,
	pub amplitude_pct: f64,
}

fn missing_column_error(column: &str) -> IoError {
	IoError::new(
		ErrorKind::InvalidData,
		format!("Missing required CSV column: {column}"),
	)
}

fn parse_f64_field(value: &str, field: &str) -> Result<f64, Box<dyn Error>> {
	let parsed = value.trim().parse::<f64>().map_err(|e| {
		IoError::new(
			ErrorKind::InvalidData,
			format!("Invalid numeric value for {field}: '{value}' ({e})"),
		)
	})?;
	Ok(parsed)
}

pub fn symbol_to_daily_csv_path(symbol: &str) -> String {
	format!("data/{}_daily.csv", symbol)
}

pub fn load_daily_quotes_by_symbol(symbol: &str) -> Result<Vec<DailyQuote>, Box<dyn Error>> {
	let file_path = symbol_to_daily_csv_path(symbol);

	if !Path::new(&file_path).exists() {
		fetch_and_store_daily_quotes(symbol, &file_path)?;
	}

	load_daily_quotes(file_path)
}

pub fn load_daily_quotes<P: AsRef<Path>>(file_path: P) -> Result<Vec<DailyQuote>, Box<dyn Error>> {
	let file = File::open(file_path)?;
	let mut reader = csv::Reader::from_reader(file);
	let headers = reader.headers()?.clone();

	let idx_date = headers
		.iter()
		.position(|h| h == "date")
		.ok_or_else(|| missing_column_error("date"))?;
	let idx_open = headers
		.iter()
		.position(|h| h == "open")
		.ok_or_else(|| missing_column_error("open"))?;
	let idx_close = headers
		.iter()
		.position(|h| h == "close")
		.ok_or_else(|| missing_column_error("close"))?;
	let idx_high = headers
		.iter()
		.position(|h| h == "high")
		.ok_or_else(|| missing_column_error("high"))?;
	let idx_low = headers
		.iter()
		.position(|h| h == "low")
		.ok_or_else(|| missing_column_error("low"))?;
	let idx_volume = headers
		.iter()
		.position(|h| h == "volume")
		.ok_or_else(|| missing_column_error("volume"))?;
	let idx_amount = headers
		.iter()
		.position(|h| h == "amount")
		.ok_or_else(|| missing_column_error("amount"))?;
	let idx_amplitude = headers
		.iter()
		.position(|h| h == "amplitude_pct")
		.ok_or_else(|| missing_column_error("amplitude_pct"))?;
	let idx_noon_close = headers.iter().position(|h| h == "noon_close");
	let idx_dividend_per_share = headers.iter().position(|h| h == "dividend_per_share");

	let mut quotes = Vec::new();

	for row in reader.records() {
		let raw = row?;
		let date = raw
			.get(idx_date)
			.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing date value"))?
			.to_string();
		let open = parse_f64_field(
			raw
				.get(idx_open)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing open value"))?,
			"open",
		)?;
		let close = parse_f64_field(
			raw
				.get(idx_close)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing close value"))?,
			"close",
		)?;
		let noon_close = match idx_noon_close {
			Some(idx) => {
				let raw_noon = raw
					.get(idx)
					.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing noon_close value"))?;
				if raw_noon.trim().is_empty() {
					close
				} else {
					parse_f64_field(raw_noon, "noon_close")?
				}
			}
			None => close,
		};
		let high = parse_f64_field(
			raw
				.get(idx_high)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing high value"))?,
			"high",
		)?;
		let low = parse_f64_field(
			raw
				.get(idx_low)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing low value"))?,
			"low",
		)?;
		let volume = parse_f64_field(
			raw
				.get(idx_volume)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing volume value"))?,
			"volume",
		)?;
		let amount = parse_f64_field(
			raw
				.get(idx_amount)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing amount value"))?,
			"amount",
		)?;
		let amplitude_pct = parse_f64_field(
			raw
				.get(idx_amplitude)
				.ok_or_else(|| IoError::new(ErrorKind::InvalidData, "Missing amplitude_pct value"))?,
			"amplitude_pct",
		)?;
		let dividend_per_share = match idx_dividend_per_share {
			Some(idx) => {
				let raw_dividend = raw.get(idx).ok_or_else(|| {
					IoError::new(ErrorKind::InvalidData, "Missing dividend_per_share value")
				})?;
				if raw_dividend.trim().is_empty() {
					0.0
				} else {
					parse_f64_field(raw_dividend, "dividend_per_share")?
				}
			}
			None => 0.0,
		};

		let quote = DailyQuote {
			date,
			open,
			noon_close,
			close,
			dividend_per_share,
			high,
			low,
			volume,
			amount,
			amplitude_pct,
		};
		quotes.push(quote);
	}

	Ok(quotes)
}
