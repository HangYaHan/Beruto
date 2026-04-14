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

