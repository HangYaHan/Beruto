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
	let result = run_backtest_for_symbol(strategy.as_mut(), symbol, &quotes, initial_capital);
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
	let result = run_backtest_for_symbol(strategy.as_mut(), symbol, &quotes, initial_capital);
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
		"Batch run started: {} tasks (manager={:?}, retry={}, force={})",
		total, config.manager, config.retry_count, config.force
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

