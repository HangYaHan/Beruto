use crate::backtest::engine::run_backtest;
use crate::backtest::result::BacktestResult;
use crate::data::data_source::{load_daily_quotes_by_symbol, symbol_to_daily_csv_path};
use crate::data::storage::{clean_results, load_all_run_records, make_run_id, save_run_record, BacktestRunRecord};
use crate::strategy::{build_strategy, find_strategy_spec, strategy_specs, StrategyConfig};
use serde_json::json;
use std::error::Error;
use std::fs;
use std::io::{self, Write};
use std::path::Path;
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

fn print_banner() {
	println!("Beruto Interactive CLI");
	if Path::new("icon.png").exists() {
		if let Ok(meta) = fs::metadata("icon.png") {
			println!("Icon loaded: icon.png ({} bytes)", meta.len());
		} else {
			println!("Icon loaded: icon.png");
		}
	} else {
		println!("Icon not found: icon.png");
	}
	println!();
}

fn print_help() {
	println!("Commands:");
	println!("  help");
	println!("  exit | quit");
	println!("  strategy list");
	println!("  strategy show <name>");
	println!("  run --symbol <code> --strategy <name> [--initial-capital <n>] [--buy-drop <n>] [--sell-rise <n>]");
	println!("  leaderboard [--top <n>]");
	println!("  clean results [--yes]");
	println!();
}

fn execute_line(line: &str) -> Result<bool, Box<dyn Error>> {
	let args: Vec<&str> = line.split_whitespace().collect();
	match args.first().copied() {
		Some("help") => {
			print_help();
			Ok(false)
		}
		Some("exit") | Some("quit") => Ok(true),
		Some("strategy") => {
			handle_strategy(&args[1..]);
			Ok(false)
		}
		Some("run") => {
			handle_run(&args[1..])?;
			Ok(false)
		}
		Some("leaderboard") => {
			handle_leaderboard(&args[1..])?;
			Ok(false)
		}
		Some("clean") => {
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
		Some("list") => {
			println!("Available strategies:");
			for spec in strategy_specs() {
				println!("  {:<12} - {}", spec.id, spec.description);
			}
		}
		Some("show") => {
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
			eprintln!("Usage: strategy list | strategy show <name>");
		}
	}
}

fn parse_flag_value<'a>(args: &'a [&'a str], flag: &str) -> Option<&'a str> {
	let mut i = 0usize;
	while i + 1 < args.len() {
		if args[i] == flag {
			return Some(args[i + 1]);
		}
		i += 1;
	}
	None
}

fn parse_f64_flag(args: &[&str], flag: &str, default: f64) -> Result<f64, Box<dyn Error>> {
	match parse_flag_value(args, flag) {
		Some(raw) => Ok(raw.parse::<f64>()?),
		None => Ok(default),
	}
}

fn handle_run(args: &[&str]) -> Result<(), Box<dyn Error>> {
	let symbol = parse_flag_value(args, "--symbol").unwrap_or("159581").to_string();
	let strategy_name = parse_flag_value(args, "--strategy").unwrap_or("buyhold");
	let initial_capital = parse_f64_flag(args, "--initial-capital", 100_000.0)?;

	let strategy_config = match strategy_name {
		"buyhold" => StrategyConfig::BuyAndHold,
		"contrarian" => StrategyConfig::Contrarian {
			buy_drop_threshold_pct: parse_f64_flag(args, "--buy-drop", -1.0)?,
			sell_rise_threshold_pct: parse_f64_flag(args, "--sell-rise", 1.0)?,
		},
		_ => {
			return Err(format!("Unknown strategy: {strategy_name}").into());
		}
	};

	let quotes = load_daily_quotes_by_symbol(&symbol)?;
	if quotes.is_empty() {
		return Err(format!("No rows found for symbol {symbol}").into());
	}

	let mut strategy = build_strategy(&strategy_config);
	let result = run_backtest(strategy.as_mut(), &quotes, initial_capital);
	print_result(&symbol, strategy.as_ref().name(), &result);

	let run_id = make_run_id();
	let now = SystemTime::now()
		.duration_since(UNIX_EPOCH)
		.unwrap_or_default()
		.as_secs();

	let parameters = match strategy_config {
		StrategyConfig::BuyAndHold => json!({
			"initial_capital": initial_capital,
		}),
		StrategyConfig::Contrarian {
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		} => json!({
			"initial_capital": initial_capital,
			"buy_drop": buy_drop_threshold_pct,
			"sell_rise": sell_rise_threshold_pct,
		}),
	};

	let record = BacktestRunRecord {
		run_id: run_id.clone(),
		timestamp_unix_secs: now,
		symbol: symbol.clone(),
		strategy_id: strategy_config.id().to_string(),
		parameters,
		data_file: symbol_to_daily_csv_path(&symbol),
		result,
	};
	let path = save_run_record(&record)?;
	println!("Saved run {} to {}", run_id, path.display());

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
		println!("No saved runs. Use 'run ...' first.");
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

fn handle_clean(args: &[&str]) -> Result<(), Box<dyn Error>> {
	if args.first().copied() != Some("results") {
		return Err("Usage: clean results [--yes]".into());
	}

	let yes = args.contains(&"--yes");
	if !yes {
		print!("This will delete saved backtest results. Continue? [y/N]: ");
		io::stdout().flush()?;
		let mut answer = String::new();
		io::stdin().read_line(&mut answer)?;
		let answer = answer.trim().to_ascii_lowercase();
		if answer != "y" && answer != "yes" {
			println!("Cancelled.");
			return Ok(());
		}
	}

	let removed = clean_results()?;
	println!("Removed {} result files.", removed);
	Ok(())
}
