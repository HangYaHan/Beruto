fn load_run_plan_file(path: &str) -> Result<RunPlanFile, Box<dyn Error>> {
	let resolved_path = resolve_run_plan_path(path)?;
	let content = fs::read_to_string(&resolved_path)?;
	let plan: RunPlanFile = serde_json::from_str(&content)?;
	Ok(plan)
}

fn resolve_run_plan_path(path: &str) -> Result<std::path::PathBuf, Box<dyn Error>> {
	let raw_path = std::path::Path::new(path);
	if raw_path.exists() {
		return Ok(raw_path.to_path_buf());
	}

	let mut candidates = Vec::new();
	if let Ok(current_dir) = std::env::current_dir() {
		candidates.push(current_dir.clone());
		candidates.push(current_dir.join("plans"));
	}

	if let Ok(exe_path) = std::env::current_exe() {
		if let Some(exe_dir) = exe_path.parent() {
			candidates.push(exe_dir.to_path_buf());
			if let Some(parent) = exe_dir.parent() {
				candidates.push(parent.to_path_buf());
				if let Some(grand_parent) = parent.parent() {
					candidates.push(grand_parent.to_path_buf());
				}
			}
		}
	}

	for base in candidates {
		let direct = base.join(path);
		if direct.exists() {
			return Ok(direct);
		}

		let plans = base.join("plans").join(path);
		if plans.exists() {
			return Ok(plans);
		}
	}

	Err(format!("Unable to locate plan file: {path}").into())
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

	let manager = match parse_flag_value(args, "--manager") {
		Some("void") => crate::manager::ManagerKind::Void,
		Some("score-rank") | Some("scorerank") => crate::manager::ManagerKind::ScoreRank,
		Some(other) => {
			return Err(format!("Unknown manager: {other}. Supported: void, score-rank").into())
		}
		None => plan
			.as_ref()
			.and_then(|p| p.manager)
			.unwrap_or_default(),
	};

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
		manager,
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
	if config.manager == crate::manager::ManagerKind::Void {
		let mut tasks = Vec::new();
		for symbol in &config.symbols {
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

		let mut seen = HashSet::new();
		tasks.retain(|task| seen.insert(task.key.clone()));
		tasks.sort_by(|a, b| a.key.cmp(&b.key));

		if tasks.is_empty() {
			return Err("No tasks generated for run command with manager=void.".into());
		}

		return Ok(tasks);
	}

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

