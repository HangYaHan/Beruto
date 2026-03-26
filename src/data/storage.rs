use crate::backtest::result::BacktestResult;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

const APP_DIR: &str = ".beruto";
const RESULTS_DIR: &str = "results";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestRunRecord {
	pub run_id: String,
	pub timestamp_unix_secs: u64,
	pub symbol: String,
	pub strategy_id: String,
	pub parameters: serde_json::Value,
	pub data_file: String,
	pub result: BacktestResult,
}

fn app_dir() -> PathBuf {
	Path::new(APP_DIR).to_path_buf()
}

pub fn results_dir() -> PathBuf {
	app_dir().join(RESULTS_DIR)
}

pub fn ensure_results_dir() -> Result<PathBuf, Box<dyn Error>> {
	let dir = results_dir();
	fs::create_dir_all(&dir)?;
	Ok(dir)
}

pub fn make_run_id() -> String {
	let now = SystemTime::now()
		.duration_since(UNIX_EPOCH)
		.unwrap_or_default();
	format!("{}-{}", now.as_secs(), now.subsec_nanos())
}

pub fn save_run_record(record: &BacktestRunRecord) -> Result<PathBuf, Box<dyn Error>> {
	let dir = ensure_results_dir()?;
	let file_name = format!("run_{}_{}_{}.json", record.run_id, record.symbol, record.strategy_id);
	let path = dir.join(file_name);
	let json = serde_json::to_string_pretty(record)?;
	fs::write(&path, json)?;
	Ok(path)
}

pub fn load_all_run_records() -> Result<Vec<BacktestRunRecord>, Box<dyn Error>> {
	let dir = results_dir();
	if !dir.exists() {
		return Ok(Vec::new());
	}

	let mut records = Vec::new();
	for entry in fs::read_dir(dir)? {
		let entry = entry?;
		let path = entry.path();
		if path.extension().and_then(|s| s.to_str()) != Some("json") {
			continue;
		}

		let content = fs::read_to_string(&path)?;
		let record: BacktestRunRecord = serde_json::from_str(&content)?;
		records.push(record);
	}

	records.sort_by(|a, b| b.timestamp_unix_secs.cmp(&a.timestamp_unix_secs));
	Ok(records)
}

pub fn clean_results() -> Result<usize, Box<dyn Error>> {
	let dir = results_dir();
	if !dir.exists() {
		return Ok(0);
	}

	let mut removed = 0usize;
	for entry in fs::read_dir(dir)? {
		let entry = entry?;
		let path = entry.path();
		if path.extension().and_then(|s| s.to_str()) == Some("json") {
			fs::remove_file(path)?;
			removed += 1;
		}
	}

	Ok(removed)
}
