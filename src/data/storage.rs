use crate::backtest::result::BacktestResult;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

const RESULTS_DIR: &str = "result";

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

fn runtime_root_dir() -> PathBuf {
	env::current_exe()
		.ok()
		.and_then(|exe| exe.parent().map(Path::to_path_buf))
		.or_else(|| env::current_dir().ok())
		.unwrap_or_else(|| PathBuf::from("."))
}

pub fn results_dir() -> PathBuf {
	runtime_root_dir().join(RESULTS_DIR)
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
		let file_name = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
		if path.extension().and_then(|s| s.to_str()) != Some("json") {
			continue;
		}
		if !file_name.starts_with("run_") {
			continue;
		}

		let content = fs::read_to_string(&path)?;
		match serde_json::from_str::<BacktestRunRecord>(&content) {
			Ok(record) => records.push(record),
			Err(err) => eprintln!("Warning: skip invalid run file {}: {}", path.display(), err),
		}
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
