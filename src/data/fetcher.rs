use serde_json::Value;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};
use std::path::Path;
use std::time::Duration;

const EASTMONEY_KLINE_URL: &str =
	"https://push2his.eastmoney.com/api/qt/stock/kline/get";
const EASTMONEY_UT: &str = "fa5fd1943c7b386f172d6893dbfba10b";

fn normalize_symbol(symbol: &str) -> Result<String, Box<dyn Error>> {
	let normalized = symbol.trim();
	if normalized.len() != 6 || !normalized.chars().all(|c| c.is_ascii_digit()) {
		return Err(IoError::new(
			ErrorKind::InvalidInput,
			format!("Invalid A-share symbol: {symbol}. Expected 6 digits, e.g. 159581"),
		)
		.into());
	}

	Ok(normalized.to_string())
}

fn to_eastmoney_secid(symbol: &str) -> Result<String, Box<dyn Error>> {
	let normalized = normalize_symbol(symbol)?;
	let first = normalized
		.chars()
		.next()
		.ok_or_else(|| IoError::new(ErrorKind::InvalidInput, "empty symbol"))?;

	let secid = match first {
		'6' | '5' | '9' => format!("1.{normalized}"),
		'0' | '1' | '2' | '3' => format!("0.{normalized}"),
		_ => {
			return Err(IoError::new(
				ErrorKind::InvalidInput,
				format!("Unsupported A-share symbol: {normalized}"),
			)
			.into())
		}
	};

	Ok(secid)
}

fn build_kline_url(secid: &str) -> String {
	format!(
		"{EASTMONEY_KLINE_URL}?secid={secid}&klt=101&fqt=1&beg=0&end=20500101&lmt=10000&ut={EASTMONEY_UT}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
	)
}

pub fn fetch_and_store_daily_quotes(symbol: &str, output_path: &str) -> Result<(), Box<dyn Error>> {
	let secid = to_eastmoney_secid(symbol)?;
	let url = build_kline_url(&secid);

	let client = reqwest::blocking::Client::builder()
		.timeout(Duration::from_secs(20))
		.build()?;

	let text = client.get(url).send()?.error_for_status()?.text()?;
	let payload: Value = serde_json::from_str(&text)?;

	let klines = payload["data"]["klines"].as_array().ok_or_else(|| {
		IoError::new(
			ErrorKind::InvalidData,
			format!("No kline data returned for symbol {symbol}"),
		)
	})?;

	if klines.is_empty() {
		return Err(IoError::new(
			ErrorKind::InvalidData,
			format!("Empty kline data returned for symbol {symbol}"),
		)
		.into());
	}

	if let Some(parent) = Path::new(output_path).parent() {
		fs::create_dir_all(parent)?;
	}

	let mut writer = csv::Writer::from_path(output_path)?;
	writer.write_record([
		"date",
		"open",
		"noon_close",
		"close",
		"high",
		"low",
		"volume",
		"amount",
		"amplitude_pct",
	])?;

	for row in klines {
		let line = row.as_str().ok_or_else(|| {
			IoError::new(ErrorKind::InvalidData, "Unexpected kline row format")
		})?;
		let parts: Vec<&str> = line.split(',').collect();
		if parts.len() < 8 {
			return Err(IoError::new(
				ErrorKind::InvalidData,
				format!("Unexpected kline row columns: {line}"),
			)
			.into());
		}

		let date = parts[0].trim();
		let open = parts[1].trim();
		let close = parts[2].trim();
		let high = parts[3].trim();
		let low = parts[4].trim();
		let volume = parts[5].trim();
		let amount = parts[6].trim();
		let amplitude_pct = parts[7].trim();

		// MVP fallback until minute-level ingestion is added.
		let noon_close = close;

		writer.write_record([
			date,
			open,
			noon_close,
			close,
			high,
			low,
			volume,
			amount,
			amplitude_pct,
		])?;
	}

	writer.flush()?;
	Ok(())
}

#[cfg(test)]
mod tests {
	use super::to_eastmoney_secid;

	#[test]
	fn secid_mapping_shanghai() {
		assert_eq!(to_eastmoney_secid("600519").unwrap(), "1.600519");
	}

	#[test]
	fn secid_mapping_shenzhen() {
		assert_eq!(to_eastmoney_secid("159581").unwrap(), "0.159581");
	}

	#[test]
	fn secid_mapping_rejects_bad_symbol() {
		assert!(to_eastmoney_secid("ABC").is_err());
	}
}
