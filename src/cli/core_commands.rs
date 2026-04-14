#[derive(Debug, Clone, Deserialize)]
struct RunPlanFile {
	#[serde(default)]
	symbols: Vec<String>,
	#[serde(default)]
	strategies: Vec<String>,
	manager: Option<crate::manager::ManagerKind>,
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
	manager: crate::manager::ManagerKind,
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
		Some("config") | Some("cfg") => {
			handle_config(&args[1..])?;
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

fn handle_config(args: &[&str]) -> Result<(), Box<dyn Error>> {
	match args.first().copied() {
		Some("show") | Some("s") => {
			let path = settings_path();
			let source = if path.exists() {
				"file"
			} else {
				"defaults"
			};
			let settings = load_settings()?;
			println!("Config source: {}", source);
			println!("Config path: {}", path.display());
			println!("{}", serde_json::to_string_pretty(&settings)?);
		}
		Some("init") => {
			let settings = AppSettings::default();
			let path = save_settings(&settings)?;
			println!("Initialized config at {}", path.display());
		}
		Some("reset") => {
			let settings = AppSettings::default();
			let path = save_settings(&settings)?;
			println!("Config reset to default structure at {}", path.display());
		}
		Some("set") => {
			if args.len() < 3 {
				return Err("Usage: config set <key> <value>".into());
			}
			let key = args[1];
			let raw_value = args[2..].join(" ");

			let settings = load_settings()?;
			let mut value = serde_json::to_value(settings)?;
			set_json_path(&mut value, key, parse_config_value(&raw_value))?;
			let updated: AppSettings = serde_json::from_value(value)?;
			let path = save_settings(&updated)?;
			println!("Updated {} in {}", key, path.display());
		}
		_ => {
			eprintln!("Usage: config <show|init|set <key> <value>|reset>");
		}
	}

	Ok(())
}

fn parse_config_value(raw: &str) -> serde_json::Value {
	if let Ok(v) = serde_json::from_str::<serde_json::Value>(raw) {
		return v;
	}

	if raw.eq_ignore_ascii_case("true") {
		return serde_json::Value::Bool(true);
	}
	if raw.eq_ignore_ascii_case("false") {
		return serde_json::Value::Bool(false);
	}
	if let Ok(v) = raw.parse::<i64>() {
		return serde_json::json!(v);
	}
	if let Ok(v) = raw.parse::<f64>() {
		if let Some(n) = serde_json::Number::from_f64(v) {
			return serde_json::Value::Number(n);
		}
	}

	serde_json::Value::String(raw.to_string())
}

fn set_json_path(root: &mut serde_json::Value, path: &str, new_value: serde_json::Value) -> Result<(), Box<dyn Error>> {
	let segments: Vec<&str> = path
		.split('.')
		.map(str::trim)
		.filter(|s| !s.is_empty())
		.collect();

	if segments.is_empty() {
		return Err("config key cannot be empty".into());
	}

	let mut current = root;
	for segment in &segments[..segments.len() - 1] {
		let obj = current
			.as_object_mut()
			.ok_or_else(|| format!("Invalid key path near '{}': not an object", segment))?;
		if !obj.contains_key(*segment) {
			obj.insert((*segment).to_string(), serde_json::json!({}));
		}
		current = obj
			.get_mut(*segment)
			.ok_or_else(|| format!("Failed to access key segment '{}'.", segment))?;
	}

	let last = segments[segments.len() - 1];
	let obj = current
		.as_object_mut()
		.ok_or_else(|| format!("Invalid key path near '{}': not an object", last))?;
	obj.insert(last.to_string(), new_value);

	Ok(())
}

fn clear_screen() {
	if cfg!(windows) {
		let _ = Command::new("cmd").args(["/C", "cls"]).status();
	} else {
		print!("\x1B[2J\x1B[H");
		let _ = io::stdout().flush();
	}
}
