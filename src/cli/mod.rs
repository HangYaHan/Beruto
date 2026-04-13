mod help;
mod parser;

use crate::backtest::engine::run_backtest;
use crate::backtest::result::BacktestResult;
use crate::backtest::visualize::write_visualization_html;
use crate::data::data_source::{load_daily_quotes_by_symbol, symbol_to_daily_csv_path};
use crate::data::fetcher::fetch_and_store_daily_quotes;
use crate::data::storage::{clean_results, ensure_results_dir, load_all_run_records, make_run_id, results_dir, save_run_record, BacktestRunRecord};
use crate::strategy::{build_strategy, find_strategy_spec, strategy_specs, StrategyConfig};
use help::{print_banner, print_help};
use parser::{parse_f64_flag, parse_f64_list_flag, parse_flag_value, parse_list_flag, parse_usize_flag, parse_usize_list_flag};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fs;
use std::io::{self, Error as IoError, ErrorKind, Write};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

pub fn run_repl() -> Result<(), Box<dyn Error>> {
	print_banner();
	print_help();

	loop {
		print!("beruto> ");
		io::stdout().flush()?;

		let mut line = String::new();
		let read = io::stdin().read_line(&mut line)?;
		if read == 0 {
			println!();
			break;
		}

		let line = line.trim();
		if line.is_empty() {
			continue;
		}

		match execute_line(line) {
			Ok(should_exit) => {
				if should_exit {
					break;
				}
			}
			Err(err) => {
				eprintln!("Error: {err}");
			}
		}
	}

	Ok(())
}

#[derive(Debug, Clone, Deserialize)]
struct RunPlanFile {
	symbols: Vec<String>,
	strategies: Vec<String>,
	initial_capital: Option<f64>,
	buy_drop_values: Option<Vec<f64>>,
	sell_rise_values: Option<Vec<f64>>,
	kdj_period_values: Option<Vec<usize>>,
	kdj_buy_threshold_values: Option<Vec<f64>>,
	kdj_sell_threshold_values: Option<Vec<f64>>,
	start_date: Option<String>,
	end_date: Option<String>,
	retry: Option<usize>,
	force: Option<bool>,
}

#[derive(Debug, Clone)]
struct RunBatchConfig {
	symbols: Vec<String>,
	strategy_ids: Vec<String>,
	initial_capital: f64,
	buy_drop_values: Vec<f64>,
	sell_rise_values: Vec<f64>,
	kdj_period_values: Vec<usize>,
	kdj_buy_threshold_values: Vec<f64>,
	kdj_sell_threshold_values: Vec<f64>,
	start_date: Option<String>,
	end_date: Option<String>,
	retry_count: usize,
	force: bool,
	plan_source: Option<String>,
}

#[derive(Debug, Clone)]
struct BacktestTask {
	symbol: String,
	strategy_config: StrategyConfig,
	initial_capital: f64,
	key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BatchTaskReport {
	index: usize,
	total: usize,
	symbol: String,
	strategy_id: String,
	task_key: String,
	status: String,
	attempts: usize,
	run_id: Option<String>,
	error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BatchCurveSummary {
	run_id: String,
	symbol: String,
	strategy_id: String,
	total_return_pct: f64,
	final_equity: f64,
	max_drawdown_pct: f64,
	equity_curve: Vec<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BatchPerformanceSummary {
	best_return_curve: Option<BatchCurveSummary>,
	worst_return_curve: Option<BatchCurveSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BatchRunSummary {
	batch_id: String,
	timestamp_unix_secs: u64,
	plan_source: Option<String>,
	total: usize,
	success: usize,
	skipped: usize,
	failed: usize,
	retry_count: usize,
	force: bool,
	summary: BatchPerformanceSummary,
	tasks: Vec<BatchTaskReport>,
}

fn execute_line(line: &str) -> Result<bool, Box<dyn Error>> {
	let args: Vec<&str> = line.split_whitespace().collect();
	match args.first().copied() {
		Some("help") | Some("h") => {
			print_help();
			Ok(false)
		}
		Some("exit") | Some("quit") | Some("q") | Some("x") => Ok(true),
		Some("clear") | Some("cls") | Some("cl") => {
			clear_screen();
			Ok(false)
		}
		Some("fetch") | Some("f") => {
			handle_fetch(&args[1..])?;
			Ok(false)
		}
		Some("strategy") | Some("st") => {
			handle_strategy(&args[1..]);
			Ok(false)
		}
		Some("backtest") | Some("bt") => {
			handle_backtest(&args[1..])?;
			Ok(false)
		}
		Some("run") => {
			handle_run_batch(&args[1..])?;
			Ok(false)
		}
		Some("leaderboard") | Some("lb") => {
			handle_leaderboard(&args[1..])?;
			Ok(false)
		}
		Some("visualize") | Some("vz") => {
			handle_visualize(&args[1..])?;
			Ok(false)
		}
		Some("clean") | Some("c") => {
			handle_clean(&args[1..])?;
			Ok(false)
		}
		Some(other) => {
			eprintln!("Unknown command: {other}. Type 'help' to list commands.");
			Ok(false)
		}
		None => Ok(false),
	}
}

fn handle_strategy(args: &[&str]) {
	match args.first().copied() {
		Some("list") | Some("l") => {
			println!("Available strategies:");
			for spec in strategy_specs() {
				println!("  {:<12} - {}", spec.id, spec.description);
			}
		}
		Some("show") | Some("sh") => {
			if args.len() < 2 {
				eprintln!("Usage: strategy show <name>");
				return;
			}
			let name = args[1];
			match find_strategy_spec(name) {
				Some(spec) => {
					println!("Name: {}", spec.name);
					println!("ID: {}", spec.id);
					println!("Description: {}", spec.description);
					println!("Usage: {}", spec.usage);
					if spec.params.is_empty() {
						println!("Params: none");
					} else {
						println!("Params:");
						for p in spec.params {
							let default = p.default_value.unwrap_or("none");
							println!("  --{:<12} default={:<8} {}", p.name, default, p.description);
						}
					}
				}
				None => eprintln!("Unknown strategy: {name}"),
			}
		}
		_ => {
			eprintln!("Usage: strategy <list|show <name>>");
		}
	}
}

fn clear_screen() {
	if cfg!(windows) {
		let _ = Command::new("cmd").args(["/C", "cls"]).status();
	} else {
		print!("\x1B[2J\x1B[H");
		let _ = io::stdout().flush();
	}
}

fn load_run_plan_file(path: &str) -> Result<RunPlanFile, Box<dyn Error>> {
	let content = fs::read_to_string(path)?;
	let plan: RunPlanFile = serde_json::from_str(&content)?;
	Ok(plan)
}

fn resolve_run_batch_config(args: &[&str]) -> Result<RunBatchConfig, Box<dyn Error>> {
	let plan_path = parse_flag_value(args, "--plan").map(ToString::to_string);
	let plan = match plan_path.as_deref() {
		Some(path) => Some(load_run_plan_file(path)?),
		None => None,
	};

	let start_date = match parse_flag_value(args, "--start-date") {
		Some(raw) => Some(validate_date_flag(raw)?),
		None => plan
			.as_ref()
			.and_then(|p| p.start_date.clone())
			.or_else(|| Some("2026-01-01".to_string())),
	};
	let end_date = match parse_flag_value(args, "--end-date") {
		Some(raw) => Some(validate_date_flag(raw)?),
		None => plan.as_ref().and_then(|p| p.end_date.clone()),
	};
	if let Some(date) = start_date.as_deref() {
		validate_date_string(date)?;
	}
	if let Some(date) = end_date.as_deref() {
		validate_date_string(date)?;
	}
	validate_date_window(start_date.as_deref(), end_date.as_deref())?;

	let mut symbols = plan
		.as_ref()
		.map(|p| p.symbols.clone())
		.unwrap_or_default();
	let cli_symbols = parse_list_flag(args, "--symbols");
	if !cli_symbols.is_empty() {
		symbols = cli_symbols;
	}
	if symbols.is_empty() {
		if let Some(single) = parse_flag_value(args, "--symbol") {
			symbols.push(single.to_string());
		}
	}

	let mut strategy_ids = plan
		.as_ref()
		.map(|p| p.strategies.clone())
		.unwrap_or_default();
	let cli_strategy_ids = parse_list_flag(args, "--strategies");
	if !cli_strategy_ids.is_empty() {
		strategy_ids = cli_strategy_ids;
	}
	if strategy_ids.is_empty() {
		if let Some(single) = parse_flag_value(args, "--strategy") {
			strategy_ids.push(single.to_string());
		}
	}
	if strategy_ids.is_empty() {
		strategy_ids.push("buyhold".to_string());
	}

	let initial_capital = match parse_flag_value(args, "--initial-capital") {
		Some(raw) => raw.parse::<f64>()?,
		None => plan
			.as_ref()
			.and_then(|p| p.initial_capital)
			.unwrap_or(100_000.0),
	};

	let buy_drop_values = {
		let cli = parse_f64_list_flag(args, "--buy-drop-values")?;
		if !cli.is_empty() {
			cli
		} else {
			plan
				.as_ref()
				.and_then(|p| p.buy_drop_values.clone())
				.filter(|v| !v.is_empty())
				.unwrap_or_else(|| vec![-1.0])
		}
	};

	let sell_rise_values = {
		let cli = parse_f64_list_flag(args, "--sell-rise-values")?;
		if !cli.is_empty() {
			cli
		} else {
			plan
				.as_ref()
				.and_then(|p| p.sell_rise_values.clone())
				.filter(|v| !v.is_empty())
				.unwrap_or_else(|| vec![1.0])
		}
	};

	let kdj_period_values = {
		let cli = parse_usize_list_flag(args, "--kdj-period-values")?;
		if !cli.is_empty() {
			cli
		} else {
			plan
				.as_ref()
				.and_then(|p| p.kdj_period_values.clone())
				.filter(|v| !v.is_empty())
				.unwrap_or_else(|| vec![9])
		}
	};

	let kdj_buy_threshold_values = {
		let cli = parse_f64_list_flag(args, "--kdj-buy-threshold-values")?;
		if !cli.is_empty() {
			cli
		} else {
			plan
				.as_ref()
				.and_then(|p| p.kdj_buy_threshold_values.clone())
				.filter(|v| !v.is_empty())
				.unwrap_or_else(|| vec![20.0])
		}
	};

	let kdj_sell_threshold_values = {
		let cli = parse_f64_list_flag(args, "--kdj-sell-threshold-values")?;
		if !cli.is_empty() {
			cli
		} else {
			plan
				.as_ref()
				.and_then(|p| p.kdj_sell_threshold_values.clone())
				.filter(|v| !v.is_empty())
				.unwrap_or_else(|| vec![80.0])
		}
	};

	let retry_count = match parse_flag_value(args, "--retry") {
		Some(raw) => raw.parse::<usize>()?,
		None => plan.as_ref().and_then(|p| p.retry).unwrap_or(1),
	};

	let force = if args.contains(&"--force") {
		true
	} else {
		plan.as_ref().and_then(|p| p.force).unwrap_or(false)
	};

	if symbols.is_empty() {
		return Err("Usage: run --symbols <a,b,...> --strategies <s1,s2,...> ... OR run --plan <path/to/plan.json>".into());
	}

	Ok(RunBatchConfig {
		symbols,
		strategy_ids,
		initial_capital,
		buy_drop_values,
		sell_rise_values,
		kdj_period_values,
		kdj_buy_threshold_values,
		kdj_sell_threshold_values,
		start_date,
		end_date,
		retry_count,
		force,
		plan_source: plan_path,
	})
}

fn expand_run_to_backtest_tasks(config: &RunBatchConfig) -> Result<Vec<BacktestTask>, Box<dyn Error>> {
	for strategy_id in &config.strategy_ids {
		if find_strategy_spec(strategy_id).is_none() {
			return Err(format!("Unknown strategy in batch run: {strategy_id}").into());
		}
	}

	let mut tasks = Vec::new();
	for symbol in &config.symbols {
		for strategy_id in &config.strategy_ids {
			match strategy_id.as_str() {
				"noop" => {
					let strategy_config = StrategyConfig::Noop;
					let key = task_key_with_date(
						symbol,
						&strategy_config,
						config.initial_capital,
						config.start_date.as_deref(),
						config.end_date.as_deref(),
					);
					tasks.push(BacktestTask {
						symbol: symbol.clone(),
						strategy_config,
						initial_capital: config.initial_capital,
						key,
					});
				}
				"buyhold" => {
					let strategy_config = StrategyConfig::BuyAndHold;
					let key = task_key_with_date(
						symbol,
						&strategy_config,
						config.initial_capital,
						config.start_date.as_deref(),
						config.end_date.as_deref(),
					);
					tasks.push(BacktestTask {
						symbol: symbol.clone(),
						strategy_config,
						initial_capital: config.initial_capital,
						key,
					});
				}
				"contrarian" => {
					for buy_drop in &config.buy_drop_values {
						for sell_rise in &config.sell_rise_values {
							let strategy_config = StrategyConfig::Contrarian {
								buy_drop_threshold_pct: *buy_drop,
								sell_rise_threshold_pct: *sell_rise,
							};
							let key = task_key_with_date(
								symbol,
								&strategy_config,
								config.initial_capital,
								config.start_date.as_deref(),
								config.end_date.as_deref(),
							);
							tasks.push(BacktestTask {
								symbol: symbol.clone(),
								strategy_config,
								initial_capital: config.initial_capital,
								key,
							});
						}
					}
				}
				"kdj" => {
					for period in &config.kdj_period_values {
						for buy_threshold in &config.kdj_buy_threshold_values {
							for sell_threshold in &config.kdj_sell_threshold_values {
								let strategy_config = StrategyConfig::Kdj {
									period: *period,
									buy_threshold: *buy_threshold,
									sell_threshold: *sell_threshold,
								};
								let key = task_key_with_date(
									symbol,
									&strategy_config,
									config.initial_capital,
									config.start_date.as_deref(),
									config.end_date.as_deref(),
								);
								tasks.push(BacktestTask {
									symbol: symbol.clone(),
									strategy_config,
									initial_capital: config.initial_capital,
									key,
								});
							}
						}
					}
				}
				_ => {}
			}
		}
	}

	let mut seen = HashSet::new();
	tasks.retain(|task| seen.insert(task.key.clone()));
	tasks.sort_by(|a, b| a.key.cmp(&b.key));

	if tasks.is_empty() {
		return Err("No tasks generated for run command.".into());
	}

	Ok(tasks)
}

fn save_batch_summary(summary: &BatchRunSummary) -> Result<(), Box<dyn Error>> {
	let dir = ensure_results_dir()?;
	let path = dir.join(format!("batch_{}.json", summary.batch_id));
	let content = serde_json::to_string_pretty(summary)?;
	fs::write(&path, content)?;
	println!("Saved batch summary to {}", path.display());
	Ok(())
}

fn compare_f64_asc(a: f64, b: f64) -> std::cmp::Ordering {
	a.partial_cmp(&b).unwrap_or(std::cmp::Ordering::Equal)
}

fn validate_date_flag(raw: &str) -> Result<String, Box<dyn Error>> {
	validate_date_string(raw)?;
	Ok(raw.to_string())
}

fn validate_date_string(raw: &str) -> Result<(i32, u32, u32), Box<dyn Error>> {
	if raw.len() != 10 {
		return Err(format!("Invalid date '{raw}': expected format YYYY-MM-DD").into());
	}
	if &raw[4..5] != "-" || &raw[7..8] != "-" {
		return Err(format!("Invalid date '{raw}': expected format YYYY-MM-DD").into());
	}

	let year = raw[0..4]
		.parse::<i32>()
		.map_err(|_| format!("Invalid date '{raw}': year must be numeric"))?;
	let month = raw[5..7]
		.parse::<u32>()
		.map_err(|_| format!("Invalid date '{raw}': month must be numeric"))?;
	let day = raw[8..10]
		.parse::<u32>()
		.map_err(|_| format!("Invalid date '{raw}': day must be numeric"))?;

	if month == 0 || month > 12 {
		return Err(format!("Invalid date '{raw}': month must be between 01 and 12").into());
	}

	let max_day = match month {
		1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
		4 | 6 | 9 | 11 => 30,
		2 => {
			if is_leap_year(year) {
				29
			} else {
				28
			}
		}
		_ => unreachable!(),
	};

	if day == 0 || day > max_day {
		return Err(format!("Invalid date '{raw}': day is out of range for month").into());
	}

	Ok((year, month, day))
}

fn is_leap_year(year: i32) -> bool {
	(year % 4 == 0 && year % 100 != 0) || year % 400 == 0
}

fn validate_date_window(start_date: Option<&str>, end_date: Option<&str>) -> Result<(), Box<dyn Error>> {
	if let (Some(start), Some(end)) = (start_date, end_date) {
		if validate_date_string(start)? > validate_date_string(end)? {
			return Err("Invalid date range: start_date must be earlier than or equal to end_date".into());
		}
	}
	Ok(())
}

fn date_in_range(date: &str, start_date: Option<&str>, end_date: Option<&str>) -> Result<bool, Box<dyn Error>> {
	let current = validate_date_string(date)?;
	if let Some(start) = start_date {
		if current < validate_date_string(start)? {
			return Ok(false);
		}
	}
	if let Some(end) = end_date {
		if current > validate_date_string(end)? {
			return Ok(false);
		}
	}
	Ok(true)
}

fn filter_quotes_by_date_range(
	quotes: Vec<crate::data::data_source::DailyQuote>,
	start_date: Option<&str>,
	end_date: Option<&str>,
) -> Result<Vec<crate::data::data_source::DailyQuote>, Box<dyn Error>> {
	let mut filtered = Vec::new();
	for quote in quotes {
		if date_in_range(&quote.date, start_date, end_date)? {
			filtered.push(quote);
		}
	}
	Ok(filtered)
}

fn extract_numeric_param(parameters: &serde_json::Value, key: &str, default: f64) -> f64 {
	parameters
		.get(key)
		.and_then(|v| v.as_f64())
		.unwrap_or(default)
}

fn task_key(symbol: &str, strategy_config: &StrategyConfig, initial_capital: f64) -> String {
	match strategy_config {
		StrategyConfig::Noop => {
			format!("{symbol}|noop|capital={initial_capital:.6}")
		}
		StrategyConfig::BuyAndHold => {
			format!("{symbol}|buyhold|capital={initial_capital:.6}")
		}
		StrategyConfig::Contrarian {
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		} => {
			format!(
				"{symbol}|contrarian|capital={initial_capital:.6}|buy_drop={buy_drop_threshold_pct:.6}|sell_rise={sell_rise_threshold_pct:.6}"
			)
		}
		StrategyConfig::Kdj {
			period,
			buy_threshold,
			sell_threshold,
		} => {
			format!(
				"{symbol}|kdj|capital={initial_capital:.6}|period={period}|buy_threshold={buy_threshold:.6}|sell_threshold={sell_threshold:.6}"
			)
		}
	}
}

fn task_key_with_date(
	symbol: &str,
	strategy_config: &StrategyConfig,
	initial_capital: f64,
	start_date: Option<&str>,
	end_date: Option<&str>,
) -> String {
	if start_date.is_none() && end_date.is_none() {
		return task_key(symbol, strategy_config, initial_capital);
	}

	let date_suffix = match (start_date, end_date) {
		(Some(start), Some(end)) => format!("|start={start}|end={end}"),
		(Some(start), None) => format!("|start={start}"),
		(None, Some(end)) => format!("|end={end}"),
		(None, None) => String::new(),
	};
	match strategy_config {
		StrategyConfig::Noop => {
			format!("{symbol}|noop|capital={initial_capital:.6}{date_suffix}")
		}
		StrategyConfig::BuyAndHold => {
			format!("{symbol}|buyhold|capital={initial_capital:.6}{date_suffix}")
		}
		StrategyConfig::Contrarian {
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		} => {
			format!(
				"{symbol}|contrarian|capital={initial_capital:.6}|buy_drop={buy_drop_threshold_pct:.6}|sell_rise={sell_rise_threshold_pct:.6}{date_suffix}"
			)
		}
		StrategyConfig::Kdj {
			period,
			buy_threshold,
			sell_threshold,
		} => {
			format!(
				"{symbol}|kdj|capital={initial_capital:.6}|period={period}|buy_threshold={buy_threshold:.6}|sell_threshold={sell_threshold:.6}{date_suffix}"
			)
		}
	}
}

fn build_existing_task_keys(records: &[BacktestRunRecord]) -> HashSet<String> {
	let mut keys = HashSet::new();
	for rec in records {
		let start_date = rec.parameters.get("start_date").and_then(|v| v.as_str());
		let end_date = rec.parameters.get("end_date").and_then(|v| v.as_str());
		let key = match rec.strategy_id.as_str() {
			"noop" => {
				let initial_capital = extract_numeric_param(&rec.parameters, "initial_capital", rec.result.initial_capital);
				task_key_with_date(&rec.symbol, &StrategyConfig::Noop, initial_capital, start_date, end_date)
			}
			"buyhold" => {
				let initial_capital = extract_numeric_param(&rec.parameters, "initial_capital", rec.result.initial_capital);
				task_key_with_date(&rec.symbol, &StrategyConfig::BuyAndHold, initial_capital, start_date, end_date)
			}
			"contrarian" => {
				let initial_capital = extract_numeric_param(&rec.parameters, "initial_capital", rec.result.initial_capital);
				let buy_drop = extract_numeric_param(&rec.parameters, "buy_drop", -1.0);
				let sell_rise = extract_numeric_param(&rec.parameters, "sell_rise", 1.0);
				task_key_with_date(
					&rec.symbol,
					&StrategyConfig::Contrarian {
						buy_drop_threshold_pct: buy_drop,
						sell_rise_threshold_pct: sell_rise,
					},
					initial_capital,
					start_date,
					end_date,
				)
			}
			"kdj" => {
				let initial_capital = extract_numeric_param(&rec.parameters, "initial_capital", rec.result.initial_capital);
				let period = rec.parameters.get("period").and_then(|v| v.as_u64()).unwrap_or(9) as usize;
				let buy_threshold = extract_numeric_param(&rec.parameters, "buy_threshold", 20.0);
				let sell_threshold = extract_numeric_param(&rec.parameters, "sell_threshold", 80.0);
				task_key_with_date(
					&rec.symbol,
					&StrategyConfig::Kdj {
						period,
						buy_threshold,
						sell_threshold,
					},
					initial_capital,
					start_date,
					end_date,
				)
			}
			_ => {
				continue;
			}
		};

		keys.insert(key);
	}

	keys
}

fn execute_single_backtest(
	symbol: &str,
	strategy_config: &StrategyConfig,
	initial_capital: f64,
) -> Result<(BacktestResult, String), Box<dyn Error>> {
	let quotes = load_daily_quotes_by_symbol(symbol)?;
	if quotes.is_empty() {
		return Err(format!("No rows found for symbol {symbol}").into());
	}

	let mut strategy = build_strategy(strategy_config);
	let result = run_backtest(strategy.as_mut(), &quotes, initial_capital);
	let strategy_name = strategy.as_ref().name().to_string();
	Ok((result, strategy_name))
}

fn execute_single_backtest_with_range(
	symbol: &str,
	strategy_config: &StrategyConfig,
	initial_capital: f64,
	start_date: Option<&str>,
	end_date: Option<&str>,
) -> Result<(BacktestResult, String), Box<dyn Error>> {
	if start_date.is_none() && end_date.is_none() {
		return execute_single_backtest(symbol, strategy_config, initial_capital);
	}

	let quotes = load_daily_quotes_by_symbol(symbol)?;
	if quotes.is_empty() {
		return Err(format!("No rows found for symbol {symbol}").into());
	}
	validate_date_window(start_date, end_date)?;
	let quotes = filter_quotes_by_date_range(quotes, start_date, end_date)?;
	if quotes.is_empty() {
		return Err(format!("No rows found for symbol {symbol} in the specified date range").into());
	}

	let mut strategy = build_strategy(strategy_config);
	let result = run_backtest(strategy.as_mut(), &quotes, initial_capital);
	let strategy_name = strategy.as_ref().name().to_string();
	Ok((result, strategy_name))
}

fn save_backtest_record(
	symbol: &str,
	strategy_config: &StrategyConfig,
	initial_capital: f64,
	start_date: Option<&str>,
	end_date: Option<&str>,
	result: BacktestResult,
) -> Result<BacktestRunRecord, Box<dyn Error>> {
	let run_id = make_run_id();
	let now = SystemTime::now()
		.duration_since(UNIX_EPOCH)
		.unwrap_or_default()
		.as_secs();

	let parameters = match strategy_config {
		StrategyConfig::Noop => json!({
			"initial_capital": initial_capital,
			"start_date": start_date,
			"end_date": end_date,
		}),
		StrategyConfig::BuyAndHold => json!({
			"initial_capital": initial_capital,
			"start_date": start_date,
			"end_date": end_date,
		}),
		StrategyConfig::Contrarian {
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		} => json!({
			"initial_capital": initial_capital,
			"buy_drop": buy_drop_threshold_pct,
			"sell_rise": sell_rise_threshold_pct,
			"start_date": start_date,
			"end_date": end_date,
		}),
		StrategyConfig::Kdj {
			period,
			buy_threshold,
			sell_threshold,
		} => json!({
			"initial_capital": initial_capital,
			"period": period,
			"buy_threshold": buy_threshold,
			"sell_threshold": sell_threshold,
			"start_date": start_date,
			"end_date": end_date,
		}),
	};

	let record = BacktestRunRecord {
		run_id: run_id.clone(),
		timestamp_unix_secs: now,
		symbol: symbol.to_string(),
		strategy_id: strategy_config.id().to_string(),
		parameters,
		data_file: symbol_to_daily_csv_path(symbol),
		result,
	};
	let path = save_run_record(&record)?;
	println!("Saved run {} to {}", run_id, path.display());

	Ok(record)
}

fn default_visualization_output_path(record: &BacktestRunRecord) -> std::path::PathBuf {
	results_dir().join(format!(
		"visualization_{}_{}_{}.html",
		record.run_id, record.symbol, record.strategy_id
	))
}

fn handle_fetch(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let symbol = args
		.first()
		.ok_or_else(|| IoError::new(ErrorKind::InvalidInput, "Usage: fetch <code>"))?;
	let output_path = symbol_to_daily_csv_path(symbol);
	fetch_and_store_daily_quotes(symbol, &output_path)?;
	println!("Fetched {symbol} data to {output_path}");
	Ok(())
}

fn handle_backtest(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let symbol = parse_flag_value(args, "--symbol").unwrap_or("159581").to_string();
	let strategy_name = parse_flag_value(args, "--strategy").unwrap_or("buyhold");
	let initial_capital = parse_f64_flag(args, "--initial-capital", 100_000.0)?;
	let start_date = parse_flag_value(args, "--start-date")
		.map(validate_date_flag)
		.transpose()?
		.or_else(|| Some("2026-01-01".to_string()));
	let end_date = parse_flag_value(args, "--end-date").map(validate_date_flag).transpose()?;
	validate_date_window(start_date.as_deref(), end_date.as_deref())?;

	let strategy_config = match strategy_name {
		"noop" => StrategyConfig::Noop,
		"buyhold" => StrategyConfig::BuyAndHold,
		"contrarian" => StrategyConfig::Contrarian {
			buy_drop_threshold_pct: parse_f64_flag(args, "--buy-drop", -1.0)?,
			sell_rise_threshold_pct: parse_f64_flag(args, "--sell-rise", 1.0)?,
		},
		"kdj" => StrategyConfig::Kdj {
			period: parse_usize_flag(args, "--kdj-period", 9)?,
			buy_threshold: parse_f64_flag(args, "--kdj-buy-threshold", 20.0)?,
			sell_threshold: parse_f64_flag(args, "--kdj-sell-threshold", 80.0)?,
		},
		_ => {
			return Err(format!("Unknown strategy: {strategy_name}").into());
		}
	};

	let (result, strategy_name) = execute_single_backtest_with_range(
		&symbol,
		&strategy_config,
		initial_capital,
		start_date.as_deref(),
		end_date.as_deref(),
	)?;
	print_result(&symbol, &strategy_name, &result);
	let record = save_backtest_record(
		&symbol,
		&strategy_config,
		initial_capital,
		start_date.as_deref(),
		end_date.as_deref(),
		result,
	)?;

	let auto_visualize = !args.contains(&"--no-visualize");
	if auto_visualize {
		if record.result.dates.is_empty() || record.result.equity_curve.is_empty() {
			eprintln!("Skip auto visualization: run has insufficient chart data.");
		} else {
			let out_path = default_visualization_output_path(&record);
			if let Some(parent) = out_path.parent() {
				std::fs::create_dir_all(parent)?;
			}
			write_visualization_html(&record, &out_path)?;
			println!("Auto visualization saved to {}", out_path.display());
		}
	}

	Ok(())
}

fn handle_run_batch(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let config = resolve_run_batch_config(args)?;
	let tasks = expand_run_to_backtest_tasks(&config)?;

	let existing_records = load_all_run_records()?;
	let existing_keys = build_existing_task_keys(&existing_records);

	let total = tasks.len();
	let mut success = 0usize;
	let mut skipped = 0usize;
	let mut failed = 0usize;
	let batch_id = make_run_id();
	let now = SystemTime::now()
		.duration_since(UNIX_EPOCH)
		.unwrap_or_default()
		.as_secs();
	let mut task_reports = Vec::with_capacity(total);
	let mut successful_curves: Vec<BatchCurveSummary> = Vec::new();

	println!(
		"Batch run started: {} tasks (retry={}, force={})",
		total, config.retry_count, config.force
	);
	if config.start_date.is_some() || config.end_date.is_some() {
		println!(
			"Date filter: start={}, end={}",
			config.start_date.as_deref().unwrap_or("(none)"),
			config.end_date.as_deref().unwrap_or("(none)")
		);
	}

	for (index, task) in tasks.into_iter().enumerate() {
		let task_index = index + 1;
		if !config.force && existing_keys.contains(&task.key) {
			skipped += 1;
			println!("[{}/{}] SKIP {} {} (already completed)", task_index, total, task.symbol, task.strategy_config.id());
			task_reports.push(BatchTaskReport {
				index: task_index,
				total,
				symbol: task.symbol,
				strategy_id: task.strategy_config.id().to_string(),
				task_key: task.key,
				status: "skipped".to_string(),
				attempts: 0,
				run_id: None,
				error: None,
			});
			continue;
		}

		let mut done = false;
		for attempt in 0..=config.retry_count {
			match execute_single_backtest_with_range(
				task.symbol.as_str(),
				&task.strategy_config,
				task.initial_capital,
				config.start_date.as_deref(),
				config.end_date.as_deref(),
			) {
				Ok((result, _strategy_name)) => {
					let persisted_result = result.clone();
					let record = save_backtest_record(
						&task.symbol,
						&task.strategy_config,
						task.initial_capital,
						config.start_date.as_deref(),
						config.end_date.as_deref(),
						result,
					)?;
					successful_curves.push(BatchCurveSummary {
						run_id: record.run_id.clone(),
						symbol: task.symbol.clone(),
						strategy_id: task.strategy_config.id().to_string(),
						total_return_pct: persisted_result.total_return_pct,
						final_equity: persisted_result.final_equity,
						max_drawdown_pct: persisted_result.max_drawdown_pct,
						equity_curve: persisted_result.equity_curve,
					});
					success += 1;
					println!("[{}/{}] OK {} {}", task_index, total, task.symbol, task.strategy_config.id());
					task_reports.push(BatchTaskReport {
						index: task_index,
						total,
						symbol: task.symbol.clone(),
						strategy_id: task.strategy_config.id().to_string(),
						task_key: task.key.clone(),
						status: "success".to_string(),
						attempts: attempt + 1,
						run_id: Some(record.run_id),
						error: None,
					});
					done = true;
					break;
				}
				Err(err) => {
					let err_text = err.to_string();
					if attempt < config.retry_count {
						println!(
							"[{}/{}] RETRY {} {} attempt {}/{} after error: {}",
							task_index,
							total,
							task.symbol,
							task.strategy_config.id(),
							attempt + 1,
							config.retry_count + 1,
							err_text
						);
					} else {
						failed += 1;
						eprintln!(
							"[{}/{}] FAIL {} {} after {} attempt(s): {}",
							task_index,
							total,
							task.symbol,
							task.strategy_config.id(),
							config.retry_count + 1,
							err_text
						);
						task_reports.push(BatchTaskReport {
							index: task_index,
							total,
							symbol: task.symbol.clone(),
							strategy_id: task.strategy_config.id().to_string(),
							task_key: task.key.clone(),
							status: "failed".to_string(),
							attempts: config.retry_count + 1,
							run_id: None,
							error: Some(err_text),
						});
					}
				}
			}
		}

		if !done {
			continue;
		}
	}

	println!(
		"Batch run finished: success={}, skipped={}, failed={}, total={}",
		success, skipped, failed, total
	);

	let best_return_curve = successful_curves
		.iter()
		.cloned()
		.max_by(|a, b| compare_f64_asc(a.total_return_pct, b.total_return_pct));
	let worst_return_curve = successful_curves
		.iter()
		.cloned()
		.min_by(|a, b| compare_f64_asc(a.total_return_pct, b.total_return_pct));

	let summary = BatchRunSummary {
		batch_id,
		timestamp_unix_secs: now,
		plan_source: config.plan_source,
		total,
		success,
		skipped,
		failed,
		retry_count: config.retry_count,
		force: config.force,
		summary: BatchPerformanceSummary {
			best_return_curve,
			worst_return_curve,
		},
		tasks: task_reports,
	};
	save_batch_summary(&summary)?;

	if failed > 0 {
		eprintln!("Some tasks failed. Check logs above for details.");
	}

	Ok(())
}

fn print_result(symbol: &str, strategy_name: &str, result: &BacktestResult) {
	println!("Symbol: {}", symbol);
	println!("Strategy: {}", strategy_name);
	println!("Initial capital: {:.2}", result.initial_capital);
	println!("Final equity:    {:.2}", result.final_equity);
	println!("Total return:    {:.2}%", result.total_return_pct);
	println!("Max drawdown:    {:.2}%", result.max_drawdown_pct);
	println!("Trades:          {}", result.trades);
	println!("Equity points:   {}", result.equity_curve.len());
}

fn handle_leaderboard(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let top = parse_flag_value(args, "--top")
		.and_then(|raw| raw.parse::<usize>().ok())
		.unwrap_or(10);

	let mut records = load_all_run_records()?;
	records.sort_by(|a, b| {
		b.result
			.total_return_pct
			.partial_cmp(&a.result.total_return_pct)
			.unwrap_or(std::cmp::Ordering::Equal)
	});

	if records.is_empty() {
		println!("No saved runs. Use 'backtest ...' first.");
		return Ok(());
	}

	println!("Leaderboard by total_return_pct:");
	println!("{:<4} {:<16} {:<8} {:<12} {:>10} {:>10}", "#", "run_id", "symbol", "strategy", "return%", "mdd%");
	for (idx, rec) in records.iter().take(top).enumerate() {
		println!(
			"{:<4} {:<16} {:<8} {:<12} {:>10.2} {:>10.2}",
			idx + 1,
			rec.run_id,
			rec.symbol,
			rec.strategy_id,
			rec.result.total_return_pct,
			rec.result.max_drawdown_pct,
		);
	}

	Ok(())
}

fn handle_visualize(args: &[&str]) -> Result<(), Box<dyn Error>> {
	if matches!(args.first().copied(), Some("batch") | Some("b")) {
		return handle_visualize_batch(&args[1..]);
	}

	let run_id = parse_flag_value(args, "--run-id").map(ToString::to_string);
	let output = parse_flag_value(args, "--output").map(ToString::to_string);

	let records = load_all_run_records()?;
	if records.is_empty() {
		return Err("No saved runs. Use 'backtest ...' first.".into());
	}

	let record = match run_id {
		Some(id) => records
			.into_iter()
			.find(|r| r.run_id == id)
			.ok_or_else(|| format!("run_id not found: {id}"))?,
		None => records
			.into_iter()
			.max_by(|a, b| a.timestamp_unix_secs.cmp(&b.timestamp_unix_secs))
			.ok_or_else(|| "No saved runs available.".to_string())?,
	};

	if record.result.dates.is_empty() || record.result.equity_curve.is_empty() {
		return Err("Selected run has insufficient chart data (dates/equity).".into());
	}

	let out_path = match output {
		Some(path) => std::path::PathBuf::from(path),
		None => default_visualization_output_path(&record),
	};
	if let Some(parent) = out_path.parent() {
		std::fs::create_dir_all(parent)?;
	}

	write_visualization_html(&record, &out_path)?;
	println!("Saved visualization to {}", out_path.display());

	Ok(())
}

#[derive(Debug, Clone, Serialize)]
struct BatchVizRow {
	run_id: String,
	symbol: String,
	strategy_id: String,
	total_return_pct: f64,
	max_drawdown_pct: f64,
	trades: usize,
	period: Option<usize>,
	buy_threshold: Option<f64>,
	sell_threshold: Option<f64>,
	start_date: Option<String>,
	end_date: Option<String>,
}

fn load_latest_batch_summary() -> Result<BatchRunSummary, Box<dyn Error>> {
	let dir = results_dir();
	if !dir.exists() {
		return Err("No result directory found. Run 'run ...' first.".into());
	}

	let mut entries: Vec<std::path::PathBuf> = fs::read_dir(&dir)?
		.filter_map(|entry| entry.ok().map(|e| e.path()))
		.filter(|path| {
			path.extension().and_then(|s| s.to_str()) == Some("json")
				&& path
					.file_name()
					.and_then(|s| s.to_str())
					.unwrap_or("")
					.starts_with("batch_")
		})
		.collect();

	if entries.is_empty() {
		return Err("No batch summary found. Run 'run ...' first.".into());
	}

	entries.sort_by_key(|p| p.file_name().map(|s| s.to_os_string()));
	let latest = entries.last().ok_or("No batch summary found.")?;
	let content = fs::read_to_string(latest)?;
	let summary: BatchRunSummary = serde_json::from_str(&content)?;
	Ok(summary)
}

fn load_batch_summary_by_id(batch_id: &str) -> Result<BatchRunSummary, Box<dyn Error>> {
	let path = results_dir().join(format!("batch_{batch_id}.json"));
	if !path.exists() {
		return Err(format!("batch_id not found: {batch_id}").into());
	}
	let content = fs::read_to_string(path)?;
	let summary: BatchRunSummary = serde_json::from_str(&content)?;
	Ok(summary)
}

fn write_batch_visualization_html(
	batch: &BatchRunSummary,
	rows: &[BatchVizRow],
	top_n: usize,
	output_path: &std::path::Path,
) -> Result<(), Box<dyn Error>> {
	let mut sorted = rows.to_vec();
	sorted.sort_by(|a, b| compare_f64_asc(b.total_return_pct, a.total_return_pct));

	let top_rows: Vec<BatchVizRow> = sorted.iter().take(top_n).cloned().collect();
	let bottom_rows: Vec<BatchVizRow> = sorted.iter().rev().take(top_n).cloned().collect();

	let rows_json = serde_json::to_string(&sorted)?;
	let top_rows_json = serde_json::to_string(&top_rows)?;
	let bottom_rows_json = serde_json::to_string(&bottom_rows)?;

	let scatter_json = serde_json::to_string(
		&sorted
			.iter()
			.map(|r| {
				json!({
					"x": r.max_drawdown_pct,
					"y": r.total_return_pct,
					"run_id": r.run_id,
					"symbol": r.symbol,
					"strategy_id": r.strategy_id,
				})
			})
			.collect::<Vec<_>>(),
	)?;

	let heatmap_json = serde_json::to_string(
		&sorted
			.iter()
			.filter_map(|r| {
				match (r.period, r.buy_threshold) {
					(Some(period), Some(buy)) => Some(json!({
						"x": period,
						"y": buy,
						"v": r.total_return_pct,
						"run_id": r.run_id,
					})),
					_ => None,
				}
			})
			.collect::<Vec<_>>(),
	)?;

	let html = format!(
		r##"<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Beruto Batch Visualization - {batch_id}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #f4f6f8;
      --card: #ffffff;
      --line: #d8e0e7;
      --text: #1f2d3a;
      --muted: #5d7283;
      --accent: #006d77;
    }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font-family: Segoe UI, Tahoma, sans-serif; }}
    .wrap {{ max-width: 1380px; margin: 0 auto; padding: 18px; }}
    .header {{ background: linear-gradient(120deg, #e0f4ef 0%, #f9f6df 100%); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; margin-top: 10px; font-size: 14px; color: var(--muted); }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 6px 8px; text-align: left; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .mono {{ font-family: Consolas, monospace; font-size: 12px; }}
    .canvas-wrap {{ height: 360px; }}
    .full {{ margin-top: 12px; }}
    @media (max-width: 980px) {{ .row {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h2 style="margin:0;">Batch Result Dashboard</h2>
      <div class="meta">
        <div><strong>batch_id:</strong> {batch_id}</div>
        <div><strong>total:</strong> {total}</div>
        <div><strong>success:</strong> {success}</div>
        <div><strong>failed:</strong> {failed}</div>
        <div><strong>rows visualized:</strong> {row_count}</div>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h3 style="margin-top:0;">Top {top_n}</h3>
        <div id="topTable"></div>
      </div>
      <div class="card">
        <h3 style="margin-top:0;">Bottom {top_n}</h3>
        <div id="bottomTable"></div>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <h3 style="margin-top:0;">Return vs Drawdown</h3>
        <div class="canvas-wrap"><canvas id="scatterChart"></canvas></div>
      </div>
      <div class="card">
        <h3 style="margin-top:0;">KDJ Heatmap (period x buy_threshold)</h3>
        <div class="canvas-wrap"><canvas id="heatmapChart"></canvas></div>
      </div>
    </div>

    <div class="card full">
      <h3 style="margin-top:0;">All Rows (sorted by return)</h3>
      <div id="allTable"></div>
    </div>
  </div>

  <script>
    const rows = {rows_json};
    const topRows = {top_rows_json};
    const bottomRows = {bottom_rows_json};
    const scatterData = {scatter_json};
    const heatmapData = {heatmap_json};

    function buildTable(targetId, data) {{
      const head = `
        <table>
          <thead>
            <tr>
              <th>run_id</th><th>symbol</th><th>strategy</th><th>ret%</th><th>mdd%</th><th>trades</th><th>period</th><th>buy</th><th>sell</th><th>start</th><th>end</th>
            </tr>
          </thead>
          <tbody>
      `;
      const body = data.map(r => `
        <tr>
          <td class="mono">${{r.run_id}}</td>
          <td>${{r.symbol}}</td>
          <td>${{r.strategy_id}}</td>
          <td>${{Number(r.total_return_pct).toFixed(2)}}</td>
          <td>${{Number(r.max_drawdown_pct).toFixed(2)}}</td>
          <td>${{r.trades}}</td>
          <td>${{r.period ?? "-"}}</td>
          <td>${{r.buy_threshold ?? "-"}}</td>
          <td>${{r.sell_threshold ?? "-"}}</td>
          <td>${{r.start_date ?? "-"}}</td>
          <td>${{r.end_date ?? "-"}}</td>
        </tr>
      `).join("");
      document.getElementById(targetId).innerHTML = head + body + "</tbody></table>";
    }}

    buildTable("topTable", topRows);
    buildTable("bottomTable", bottomRows);
    buildTable("allTable", rows);

    new Chart(document.getElementById("scatterChart"), {{
      type: "scatter",
      data: {{
        datasets: [{{
          label: "runs",
          data: scatterData,
          pointRadius: 4,
          backgroundColor: "rgba(0,109,119,0.65)",
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: "max_drawdown_pct" }} }},
          y: {{ title: {{ display: true, text: "total_return_pct" }} }}
        }},
        plugins: {{
          tooltip: {{
            callbacks: {{
              label: (ctx) => {{
                const d = ctx.raw;
                return `${{d.run_id}} ret=${{d.y.toFixed(2)}} mdd=${{d.x.toFixed(2)}}`;
              }}
            }}
          }}
        }}
      }}
    }});

    new Chart(document.getElementById("heatmapChart"), {{
      type: "bubble",
      data: {{
        datasets: [{{
          label: "KDJ points",
          data: heatmapData.map(p => ({{ x: p.x, y: p.y, r: Math.max(4, Math.min(14, Math.abs(p.v) / 3 + 4)), v: p.v, run_id: p.run_id }})),
          backgroundColor: heatmapData.map(p => p.v >= 0 ? "rgba(15,157,88,0.55)" : "rgba(217,48,37,0.55)"),
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ title: {{ display: true, text: "period" }} }},
          y: {{ title: {{ display: true, text: "buy_threshold" }} }}
        }},
        plugins: {{
          tooltip: {{
            callbacks: {{
              label: (ctx) => {{
                const d = ctx.raw;
                return `${{d.run_id}} ret=${{Number(d.v).toFixed(2)}}`;
              }}
            }}
          }}
        }}
      }}
    }});
  </script>
</body>
</html>
"##,
		batch_id = batch.batch_id,
		total = batch.total,
		success = batch.success,
		failed = batch.failed,
		row_count = sorted.len(),
		top_n = top_n,
		rows_json = rows_json,
		top_rows_json = top_rows_json,
		bottom_rows_json = bottom_rows_json,
		scatter_json = scatter_json,
		heatmap_json = heatmap_json,
	);

	std::fs::write(output_path, html)?;
	Ok(())
}

fn handle_visualize_batch(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let batch_id = parse_flag_value(args, "--batch-id").map(ToString::to_string);
	let symbol_filter = parse_flag_value(args, "--symbol").map(ToString::to_string);
	let top_n = parse_usize_flag(args, "--top", 20)?;
	let output = parse_flag_value(args, "--output").map(ToString::to_string);

	let batch = match batch_id {
		Some(id) => load_batch_summary_by_id(&id)?,
		None => load_latest_batch_summary()?,
	};

	let records = load_all_run_records()?;
	let record_map: HashMap<String, BacktestRunRecord> = records
		.into_iter()
		.map(|r| (r.run_id.clone(), r))
		.collect();

	let mut rows = Vec::new();
	for task in &batch.tasks {
		if task.status != "success" {
			continue;
		}
		let run_id = match &task.run_id {
			Some(v) => v,
			None => continue,
		};
		let record = match record_map.get(run_id) {
			Some(v) => v,
			None => continue,
		};

		if let Some(symbol) = &symbol_filter {
			if &record.symbol != symbol {
				continue;
			}
		}

		rows.push(BatchVizRow {
			run_id: record.run_id.clone(),
			symbol: record.symbol.clone(),
			strategy_id: record.strategy_id.clone(),
			total_return_pct: record.result.total_return_pct,
			max_drawdown_pct: record.result.max_drawdown_pct,
			trades: record.result.trades,
			period: record.parameters.get("period").and_then(|v| v.as_u64()).map(|v| v as usize),
			buy_threshold: record.parameters.get("buy_threshold").and_then(|v| v.as_f64()),
			sell_threshold: record.parameters.get("sell_threshold").and_then(|v| v.as_f64()),
			start_date: record.parameters.get("start_date").and_then(|v| v.as_str()).map(ToString::to_string),
			end_date: record.parameters.get("end_date").and_then(|v| v.as_str()).map(ToString::to_string),
		});
	}

	if rows.is_empty() {
		return Err("No rows available for visualize batch with current filters.".into());
	}

	let out_path = match output {
		Some(path) => std::path::PathBuf::from(path),
		None => results_dir().join(format!("batch_visualization_{}.html", batch.batch_id)),
	};
	if let Some(parent) = out_path.parent() {
		std::fs::create_dir_all(parent)?;
	}

	write_batch_visualization_html(&batch, &rows, top_n, &out_path)?;
	println!("Saved batch visualization to {}", out_path.display());
	Ok(())
}

fn handle_clean(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let target = args.first().copied().ok_or_else(|| {
		IoError::new(ErrorKind::InvalidInput, "Usage: clean <results|data> [--yes]")
	})?;

	if !matches!(target, "results" | "res" | "r" | "data" | "d") {
		return Err("Usage: clean <results|data> [--yes]".into());
	}

	let yes = args.contains(&"--yes");
	if !yes {
		if matches!(target, "results" | "res" | "r") {
			print!("This will delete saved backtest results. Continue? [y/N]: ");
		} else {
			print!("This will delete files under data/. Continue? [y/N]: ");
		}
		io::stdout().flush()?;
		let mut answer = String::new();
		io::stdin().read_line(&mut answer)?;
		let answer = answer.trim().to_ascii_lowercase();
		if answer != "y" && answer != "yes" {
			println!("Cancelled.");
			return Ok(());
		}
	}

	if matches!(target, "results" | "res" | "r") {
		let removed = clean_results()?;
		println!("Removed {} result files.", removed);
	} else {
		let mut removed = 0usize;
		if let Ok(entries) = fs::read_dir("data") {
			for entry in entries {
				let entry = entry?;
				let path = entry.path();
				if path.is_file() {
					fs::remove_file(path)?;
					removed += 1;
				}
			}
		}
		println!("Removed {} data files.", removed);
	}

	Ok(())
}
