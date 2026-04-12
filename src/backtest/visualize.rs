use std::error::Error;
use std::path::Path;

use crate::data::storage::BacktestRunRecord;

fn build_position_ranges(events: &[crate::backtest::result::TradeEvent], total_len: usize) -> Vec<(usize, usize)> {
	let mut ranges = Vec::new();
	let mut entry: Option<usize> = None;

	for event in events {
		if event.side == "buy" {
			if entry.is_none() {
				entry = Some(event.index);
			}
		} else if event.side == "sell" {
			if let Some(start) = entry.take() {
				ranges.push((start, event.index));
			}
		}
	}

	if let Some(start) = entry {
		if total_len > 0 {
			ranges.push((start, total_len - 1));
		}
	}

	ranges
}

pub fn write_visualization_html(record: &BacktestRunRecord, output_path: &Path) -> Result<(), Box<dyn Error>> {
	let result = &record.result;
	let labels_json = serde_json::to_string(&result.dates)?;
	let equity_json = serde_json::to_string(&result.equity_curve)?;
	let closes_json = serde_json::to_string(&result.close_prices)?;
	let highs_json = serde_json::to_string(&result.high_prices)?;
	let lows_json = serde_json::to_string(&result.low_prices)?;
	let events_json = serde_json::to_string(&result.trade_events)?;
	let position_ranges_json = serde_json::to_string(&build_position_ranges(&result.trade_events, result.dates.len()))?;

	let drawdown_peak = result.max_drawdown_span.peak_index;
	let drawdown_trough = result.max_drawdown_span.trough_index;
	let kdj_period = record
		.parameters
		.get("period")
		.and_then(|v| v.as_u64())
		.unwrap_or(9);

  let html = format!(
    r##"<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Beruto Visualization - {run_id}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
  <style>
    :root {{
      --bg: #f3f6f8;
      --card: #ffffff;
      --line: #dce3e8;
      --text: #1a2a33;
      --muted: #4d6673;
      --buy: #0f9d58;
      --sell: #d93025;
      --accent: #006d77;
      --warn: #e9c46a;
    }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font-family: Segoe UI, Tahoma, sans-serif; }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
    .header {{ background: linear-gradient(120deg, #d5f3ef 0%, #f8f3d9 100%); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; margin-top: 10px; font-size: 14px; color: var(--muted); }}
    .toolbar {{ margin-top: 10px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .toolbar button {{ border: 1px solid var(--line); background: #fff; color: var(--text); border-radius: 8px; padding: 6px 10px; cursor: pointer; }}
    .toolbar small {{ color: var(--muted); }}
    .card {{ margin-top: 14px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px; }}
    canvas {{ width: 100%; height: 320px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h2 style="margin:0;">Beruto Backtest Visualization</h2>
      <div class="meta">
        <div><strong>run_id:</strong> {run_id}</div>
        <div><strong>symbol:</strong> {symbol}</div>
        <div><strong>strategy:</strong> {strategy}</div>
        <div><strong>return:</strong> {ret:.2}%</div>
        <div><strong>max drawdown:</strong> {mdd:.2}%</div>
        <div><strong>trades:</strong> {trades}</div>
      </div>
      <div class="toolbar">
        <button type="button" onclick="resetZoomAll()">Reset Zoom</button>
        <small>Mouse wheel: zoom, drag: zoom range, hold Ctrl and drag: pan</small>
      </div>
    </div>
    <div class="card"><canvas id="equityChart"></canvas></div>
    <div class="card"><canvas id="priceChart"></canvas></div>
    <div class="card"><canvas id="kdjChart"></canvas></div>
  </div>

  <script>
    const labels = {labels_json};
    const equity = {equity_json};
    const closes = {closes_json};
    const highs = {highs_json};
    const lows = {lows_json};
    const events = {events_json};
    const positionRanges = {position_ranges_json};
    const drawdownPeak = {drawdown_peak};
    const drawdownTrough = {drawdown_trough};
    const kdjPeriod = {kdj_period};

    function computeKdj(period, highsArr, lowsArr, closesArr) {{
      const k = [];
      const d = [];
      const j = [];
      let kPrev = 50.0;
      let dPrev = 50.0;

      for (let i = 0; i < closesArr.length; i++) {{
        const start = Math.max(0, i - period + 1);
        let hh = -Infinity;
        let ll = Infinity;
        for (let p = start; p <= i; p++) {{
          hh = Math.max(hh, highsArr[p]);
          ll = Math.min(ll, lowsArr[p]);
        }}
        const range = hh - ll;
        const rsv = Math.abs(range) < Number.EPSILON ? 50.0 : Math.max(0, Math.min(100, (closesArr[i] - ll) / range * 100));
        const kNow = (2 * kPrev + rsv) / 3;
        const dNow = (2 * dPrev + kNow) / 3;
        const jNow = 3 * kNow - 2 * dNow;
        k.push(kNow);
        d.push(dNow);
        j.push(jNow);
        kPrev = kNow;
        dPrev = dNow;
      }}
      return {{ k, d, j }};
    }}

    function asPoints(arr) {{
      return arr.map((v, i) => ({{ x: i, y: v }}));
    }}

    const buyPoints = events.filter(e => e.side === "buy").map(e => ({{ x: e.index, y: e.price }}));
    const sellPoints = events.filter(e => e.side === "sell").map(e => ({{ x: e.index, y: e.price }}));

    const shadingPlugin = {{
      id: "berutoShading",
      beforeDatasetsDraw(chart) {{
        const {{ctx, chartArea, scales}} = chart;
        if (!chartArea) return;
        const x = scales.x;

        ctx.save();
        for (const [start, end] of positionRanges) {{
          const x1 = x.getPixelForValue(start);
          const x2 = x.getPixelForValue(end);
          ctx.fillStyle = "rgba(15,157,88,0.08)";
          ctx.fillRect(Math.min(x1, x2), chartArea.top, Math.abs(x2 - x1), chartArea.bottom - chartArea.top);
        }}

        if (drawdownTrough >= drawdownPeak) {{
          const x1 = x.getPixelForValue(drawdownPeak);
          const x2 = x.getPixelForValue(drawdownTrough);
          ctx.fillStyle = "rgba(233,196,106,0.18)";
          ctx.fillRect(Math.min(x1, x2), chartArea.top, Math.abs(x2 - x1), chartArea.bottom - chartArea.top);
        }}
        ctx.restore();
      }}
    }};

    Chart.register(shadingPlugin);

    const commonOptions = {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: "index", intersect: false }},
      plugins: {{
        legend: {{ position: "top" }},
        zoom: {{
          limits: {{ x: {{ min: 0, max: labels.length - 1 }} }},
          pan: {{ enabled: true, mode: "x", modifierKey: "ctrl" }},
          zoom: {{
            mode: "x",
            wheel: {{ enabled: true }},
            pinch: {{ enabled: true }},
            drag: {{ enabled: true }}
          }}
        }}
      }},
      scales: {{
        x: {{ type: "linear", ticks: {{ callback: (v) => labels[v] ?? "" }} }}
      }}
    }};

    const equityChart = new Chart(document.getElementById("equityChart"), {{
      type: "line",
      data: {{
        datasets: [
          {{
            label: "Equity",
            data: asPoints(equity),
            borderColor: "#006d77",
            pointRadius: 0,
            borderWidth: 2,
            tension: 0.15,
          }}
        ]
      }},
      options: commonOptions
    }});

    const priceChart = new Chart(document.getElementById("priceChart"), {{
      type: "line",
      data: {{
        datasets: [
          {{ label: "Close", data: asPoints(closes), borderColor: "#2a9d8f", pointRadius: 0, borderWidth: 1.8, tension: 0.1 }},
          {{ label: "Buy", data: buyPoints, showLine: false, pointRadius: 5, pointBackgroundColor: "#0f9d58" }},
          {{ label: "Sell", data: sellPoints, showLine: false, pointRadius: 5, pointBackgroundColor: "#d93025" }}
        ]
      }},
      options: commonOptions
    }});

    const kdj = computeKdj(kdjPeriod, highs, lows, closes);
    const kdjChart = new Chart(document.getElementById("kdjChart"), {{
      type: "line",
      data: {{
        datasets: [
          {{ label: "K", data: asPoints(kdj.k), borderColor: "#1d3557", pointRadius: 0, borderWidth: 1.4, tension: 0.1 }},
          {{ label: "D", data: asPoints(kdj.d), borderColor: "#457b9d", pointRadius: 0, borderWidth: 1.4, tension: 0.1 }},
          {{ label: "J", data: asPoints(kdj.j), borderColor: "#e76f51", pointRadius: 0, borderWidth: 1.4, tension: 0.1 }}
        ]
      }},
      options: {{
        ...commonOptions,
        scales: {{
          ...commonOptions.scales,
          y: {{ suggestedMin: 0, suggestedMax: 100 }}
        }}
      }}
    }});

    function resetZoomAll() {{
      equityChart.resetZoom();
      priceChart.resetZoom();
      kdjChart.resetZoom();
    }}
  </script>
</body>
</html>
"##,
		run_id = record.run_id,
		symbol = record.symbol,
		strategy = record.strategy_id,
		ret = result.total_return_pct,
		mdd = result.max_drawdown_pct,
		trades = result.trades,
		labels_json = labels_json,
		equity_json = equity_json,
		closes_json = closes_json,
		highs_json = highs_json,
		lows_json = lows_json,
		events_json = events_json,
		position_ranges_json = position_ranges_json,
		drawdown_peak = drawdown_peak,
		drawdown_trough = drawdown_trough,
		kdj_period = kdj_period,
	);

	std::fs::write(output_path, html)?;
	Ok(())
}