fn handle_visualize(args: &[&str]) -> Result<(), Box<dyn Error>> {
	if matches!(args.first().copied(), Some("batch") | Some("b")) {
		return handle_visualize_batch(&args[1..]);
	}

	let run_id = parse_flag_value(args, "--run-id").map(ToString::to_string);
	let output = parse_flag_value(args, "--output").map(ToString::to_string);

	let records = load_all_run_records()?;
	if records.is_empty() {
		return Err("No saved runs. Use 'run ...' first.".into());
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
