const BERUTO_BANNER: [&str; 7] = [
	"BBBBBBB   EEEEEEE   RRRRRRR    U     U   TTTTTTT   OOOOOOO",
	"B     B   E         R     R    U     U      T      O     O",
	"B     B   E         R     R    U     U      T      O     O",
	"BBBBBBB   EEEEE     RRRRRRR    U     U      T      O     O",
	"B     B   E         R   R      U     U      T      O     O",
	"B     B   E         R    R     U     U      T      O     O",
	"BBBBBBB   EEEEEEE   R     R     UUUUU       T      OOOOOOO",
];

pub fn print_banner() {
	let max_width = BERUTO_BANNER
		.iter()
		.map(|line| line.chars().count())
		.max()
		.unwrap_or(0);
	let border = "=".repeat(max_width + 10);

	println!("{}", border);
	for line in BERUTO_BANNER {
		println!("=    {}    =", line);
	}
	println!("{}", border);
	println!();
}

pub fn print_startup_help() {
	println!("Commands:");
	println!("  help");
	println!("  exit | quit");
	println!("  clear");
	println!("  fetch");
	println!("  strategy");
	println!("  config");
	println!("  run");
	println!("  leaderboard");
	println!("  visualize");
	println!("  clean");
	println!();
}

pub fn print_help() {
	println!("Commands:");
	println!("  help");
	println!("  exit | quit");
	println!("  clear");
	println!("  fetch <code>");
	println!("  strategy <list|show <name>>");
	println!("  config <show|init|set <key> <value>|reset>");
	println!("  run --symbols <a,b,...> --strategies <s1,s2,...> [--manager <void|score-rank>] [--initial-capital <n>] [--buy-drop-values <v1,v2,...>] [--sell-rise-values <v1,v2,...>] [--kdj-period-values <v1,v2,...>] [--kdj-buy-threshold-values <v1,v2,...>] [--kdj-sell-threshold-values <v1,v2,...>] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--retry <n>] [--force]  (default start-date: 2026-01-01)");
	println!("  run --plan <path/to/plan.json> [--manager <void|score-rank>] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--retry <n>] [--force]");
	println!("  leaderboard [--top <n>]");
	println!("  visualize [--run-id <id>] [--output <path/to/report.html>]");
	println!("  visualize batch [--batch-id <id>] [--symbol <code>] [--top <n>] [--output <path/to/dashboard.html>]");
	println!("  clean <results|data> [--yes]");
	println!();
}
