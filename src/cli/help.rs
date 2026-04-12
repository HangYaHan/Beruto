use std::fs;
use std::path::Path;

pub fn print_banner() {
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

pub fn print_help() {
	println!("Commands:");
	println!("  help");
	println!("  exit | quit");
	println!("  clear");
	println!("  fetch <code>");
	println!("  strategy <list|show <name>>");
	println!("  backtest --symbol <code> --strategy <name> [--initial-capital <n>] [--buy-drop <n>] [--sell-rise <n>] [--kdj-period <n>] [--kdj-buy-threshold <n>] [--kdj-sell-threshold <n>] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--no-visualize]  (default start-date: 2026-01-01)");
	println!("  run --symbols <a,b,...> --strategies <s1,s2,...> [--initial-capital <n>] [--buy-drop-values <v1,v2,...>] [--sell-rise-values <v1,v2,...>] [--kdj-period-values <v1,v2,...>] [--kdj-buy-threshold-values <v1,v2,...>] [--kdj-sell-threshold-values <v1,v2,...>] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--retry <n>] [--force]  (default start-date: 2026-01-01)");
	println!("  run --plan <path/to/plan.json> [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--retry <n>] [--force]");
	println!("  leaderboard [--top <n>]");
	println!("  visualize [--run-id <id>] [--output <path/to/report.html>]");
	println!("  visualize batch [--batch-id <id>] [--symbol <code>] [--top <n>] [--output <path/to/dashboard.html>]");
	println!("  clean <results|data> [--yes]");
	println!();
}
