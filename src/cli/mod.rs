use crate::backtest::engine::run_backtest;
use crate::backtest::result::BacktestResult;
use crate::data::data_source::{load_daily_quotes_by_symbol, symbol_to_daily_csv_path};
use crate::data::settings::{AppSettings, load_settings, save_settings};
use crate::data::storage::{
    BacktestRunRecord, clean_results, load_all_run_records, make_run_id, save_run_record,
};
use crate::strategy::{
    StrategyConfig, build_strategy, find_strategy_spec, strategy_config_from_values, strategy_specs,
};
use serde_json::json;
use std::collections::HashMap;
use std::error::Error;
use std::io::{self, Write};
use std::time::{SystemTime, UNIX_EPOCH};

pub fn run_repl() -> Result<(), Box<dyn Error>> {
    let mut settings = load_settings()?;

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

        match execute_line(line, &mut settings) {
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
    let banner = [
        "===============================================================",
        "=                                                             =",
        "=  BBBBB   EEEEE  RRRRR   U   U  TTTTT   OOO                  =",
        "=  B    B  E      R    R  U   U    T    O   O                 =",
        "=  BBBBB   EEEE   RRRRR   U   U    T    O   O                 =",
        "=  B    B  E      R   R   U   U    T    O   O                 =",
        "=  BBBBB   EEEEE  R    R   UUU     T     OOO                  =",
        "=                                                             =",
        "===============================================================",
    ];

    for line in banner {
        println!("{line}");
    }
    println!();
}

fn print_help() {
    println!("Commands:");
    println!("  help | h | ?");
    println!("  exit | quit | q");
    println!("  backtest | bt");
    println!("  strategy | strat | st list | ls");
    println!("  strategy | strat | st show | sh <name>");
    println!("  run | r [legacy-compatible, prefer 'bt']");
    println!("  leaderboard | lb [--top <n>]");
    println!("  clean | cl results | res [--yes]");
    println!("  cls | clear");
    println!("  settings | set [args...] (same as bt settings)");
    println!();
}

fn print_backtest_help() {
    println!("Backtest subsystem commands:");
    println!("  help | h | ?");
    println!("  exit | quit | q | back");
    println!("  run | r                             # interactive one-by-one prompts");
    println!("  run | r --strategy <id> [flags...]  # quick mode with overrides");
    println!("  <strategy-id>                        # shortcut to guided run");
    println!("  strategy | st list | ls");
    println!("  strategy | st show | sh <id>");
    println!("  settings | set show [strategy]");
    println!("  settings | set set global symbol <code>");
    println!("  settings | set set global initial-capital <n>");
    println!("  settings | set set <strategy> <param> <value>");
    println!("  settings | set reset <strategy>");
    println!("  settings | set save");
    println!();
}

fn execute_line(line: &str, settings: &mut AppSettings) -> Result<bool, Box<dyn Error>> {
    let args: Vec<&str> = line.split_whitespace().collect();
    match args.first().copied() {
        Some("help") | Some("h") | Some("?") => {
            print_help();
            Ok(false)
        }
        Some("exit") | Some("quit") | Some("q") => Ok(true),
        Some("backtest") | Some("bt") => {
            run_backtest_shell(settings)?;
            Ok(false)
        }
        Some("strategy") | Some("strat") | Some("st") => {
            handle_strategy(&args[1..]);
            Ok(false)
        }
        Some("run") | Some("r") => {
            println!("Tip: use 'bt' and then 'run' for the new guided flow.");
            handle_backtest_run(&args[1..], settings)?;
            Ok(false)
        }
        Some("leaderboard") | Some("lb") => {
            handle_leaderboard(&args[1..])?;
            Ok(false)
        }
        Some("clean") | Some("cl") => {
            handle_clean(&args[1..])?;
            Ok(false)
        }
        Some("cls") | Some("clear") => {
            handle_cls();
            Ok(false)
        }
        Some("settings") | Some("set") => {
            handle_settings(&args[1..], settings)?;
            Ok(false)
        }
        Some(other) => {
            eprintln!("Unknown command: {other}. Type 'help' to list commands.");
            Ok(false)
        }
        None => Ok(false),
    }
}

fn run_backtest_shell(settings: &mut AppSettings) -> Result<(), Box<dyn Error>> {
    print_backtest_help();

    loop {
        print!("bt> ");
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

        let args: Vec<&str> = line.split_whitespace().collect();
        match args.first().copied() {
            Some("help") | Some("h") | Some("?") => print_backtest_help(),
            Some("exit") | Some("quit") | Some("q") | Some("back") => break,
            Some("run") | Some("r") => {
                if let Err(err) = handle_backtest_run(&args[1..], settings) {
                    eprintln!("Error: {err}");
                }
            }
            Some("strategy") | Some("strat") | Some("st") => handle_strategy(&args[1..]),
            Some("settings") | Some("set") => {
                if let Err(err) = handle_settings(&args[1..], settings) {
                    eprintln!("Error: {err}");
                }
            }
            Some(other) => {
                if find_strategy_spec(other).is_some() {
                    if let Err(err) = run_interactive_backtest(settings, Some(other)) {
                        eprintln!("Error: {err}");
                    }
                } else {
                    eprintln!("Unknown bt command: {other}. Type 'help' to list commands.");
                }
            }
            None => {}
        }
    }

    Ok(())
}

fn handle_strategy(args: &[&str]) {
    match args.first().copied() {
        Some("list") | Some("ls") => {
            println!("Available strategies:");
            for spec in strategy_specs() {
                println!("  {:<12} - {}", spec.id, spec.description);
            }
        }
        Some("show") | Some("sh") => {
            if args.len() < 2 {
                eprintln!("Usage: strategy show|sh <name>");
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
                            println!(
                                "  --{:<14} default={:<8} {}",
                                p.name, default, p.description
                            );
                        }
                    }
                }
                None => eprintln!("Unknown strategy: {name}"),
            }
        }
        _ => {
            eprintln!("Usage: strategy|st list|ls | strategy|st show|sh <name>");
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

fn parse_string_flag(args: &[&str], flag: &str, default: &str) -> String {
    parse_flag_value(args, flag)
        .unwrap_or(default)
        .trim()
        .to_string()
}

fn handle_backtest_run(args: &[&str], settings: &AppSettings) -> Result<(), Box<dyn Error>> {
    if args.is_empty() {
        return run_interactive_backtest(settings, None);
    }

    run_quick_backtest(args, settings)
}

fn run_quick_backtest(args: &[&str], settings: &AppSettings) -> Result<(), Box<dyn Error>> {
    let strategy_id = parse_flag_value(args, "--strategy").unwrap_or("buyhold");
    if find_strategy_spec(strategy_id).is_none() {
        return Err(format!("Unknown strategy: {strategy_id}").into());
    }

    let symbol = parse_string_flag(args, "--symbol", &settings.default_symbol);
    let initial_capital =
        parse_f64_flag(args, "--initial-capital", settings.default_initial_capital)?;

    let mut param_values = settings.strategy_values(strategy_id);
    if let Some(spec) = find_strategy_spec(strategy_id) {
        for param in spec.params {
            let flag = format!("--{}", param.name);
            if let Some(raw) = parse_flag_value(args, &flag) {
                let parsed = raw.parse::<f64>()?;
                param_values.insert(param.name.to_string(), parsed);
            }
        }
    }

    let strategy_config = strategy_config_from_values(strategy_id, &param_values)
        .map_err(|err| -> Box<dyn Error> { err.into() })?;

    execute_backtest(&symbol, strategy_config, initial_capital)
}

fn run_interactive_backtest(
    settings: &AppSettings,
    preselected_strategy: Option<&str>,
) -> Result<(), Box<dyn Error>> {
    println!("Interactive run: press Enter to accept defaults.");
    println!("Available strategies: buyhold, contrarian, macd, kdj");

    let strategy_id = match preselected_strategy {
        Some(strategy) => strategy.to_string(),
        None => prompt_string("Strategy", "buyhold")?,
    };
    if find_strategy_spec(&strategy_id).is_none() {
        return Err(format!("Unknown strategy: {strategy_id}").into());
    }

    let symbol = prompt_string("Symbol", &settings.default_symbol)?;
    let initial_capital = prompt_f64("Initial capital", settings.default_initial_capital)?;

    let mut values = settings.strategy_values(&strategy_id);
    if let Some(spec) = find_strategy_spec(&strategy_id) {
        for param in spec.params {
            let current = values.get(param.name).copied().unwrap_or(0.0);
            let label = format!("{} ({})", param.name, param.description);
            let value = prompt_f64(&label, current)?;
            values.insert(param.name.to_string(), value);
        }
    }

    let strategy_config = strategy_config_from_values(&strategy_id, &values)
        .map_err(|err| -> Box<dyn Error> { err.into() })?;

    execute_backtest(&symbol, strategy_config, initial_capital)
}

fn prompt_string(label: &str, default: &str) -> Result<String, Box<dyn Error>> {
    print!("{} [{}]: ", label, default);
    io::stdout().flush()?;

    let mut line = String::new();
    io::stdin().read_line(&mut line)?;
    let line = line.trim();
    if line.is_empty() {
        Ok(default.to_string())
    } else {
        Ok(line.to_string())
    }
}

fn prompt_f64(label: &str, default: f64) -> Result<f64, Box<dyn Error>> {
    loop {
        print!("{} [{:.4}]: ", label, default);
        io::stdout().flush()?;

        let mut line = String::new();
        io::stdin().read_line(&mut line)?;
        let line = line.trim();
        if line.is_empty() {
            return Ok(default);
        }

        match line.parse::<f64>() {
            Ok(value) => return Ok(value),
            Err(_) => eprintln!("Invalid number: {line}"),
        }
    }
}

fn strategy_parameters_json(
    strategy_config: &StrategyConfig,
    initial_capital: f64,
) -> serde_json::Value {
    match strategy_config {
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
        StrategyConfig::Macd {
            fast_period,
            slow_period,
            signal_period,
        } => json!({
            "initial_capital": initial_capital,
            "indicator": "macd",
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
        }),
        StrategyConfig::Kdj { period } => json!({
            "initial_capital": initial_capital,
            "indicator": "kdj",
            "period": period,
        }),
    }
}

fn execute_backtest(
    symbol: &str,
    strategy_config: StrategyConfig,
    initial_capital: f64,
) -> Result<(), Box<dyn Error>> {
    let quotes = load_daily_quotes_by_symbol(symbol)?;
    if quotes.is_empty() {
        return Err(format!("No rows found for symbol {symbol}").into());
    }

    let mut strategy = build_strategy(&strategy_config);
    let result = run_backtest(strategy.as_mut(), &quotes, initial_capital);
    print_result(symbol, strategy.as_ref().name(), &result);

    let run_id = make_run_id();
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    let record = BacktestRunRecord {
        run_id: run_id.clone(),
        timestamp_unix_secs: now,
        symbol: symbol.to_string(),
        strategy_id: strategy_config.id().to_string(),
        parameters: strategy_parameters_json(&strategy_config, initial_capital),
        data_file: symbol_to_daily_csv_path(symbol),
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
    println!(
        "{:<4} {:<16} {:<8} {:<12} {:>10} {:>10}",
        "#", "run_id", "symbol", "strategy", "return%", "mdd%"
    );
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
    match args.first().copied() {
        Some("results") | Some("res") => {}
        _ => return Err("Usage: clean|cl results|res [--yes]".into()),
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

fn handle_cls() {
    // ANSI clear-screen + cursor-home; widely supported by modern terminals.
    print!("\x1B[2J\x1B[1;1H");
    let _ = io::stdout().flush();
}

fn handle_settings(args: &[&str], settings: &mut AppSettings) -> Result<(), Box<dyn Error>> {
    if args.is_empty() {
        print_settings(settings, None);
        return Ok(());
    }

    match args[0] {
        "show" | "list" => {
            let strategy = args.get(1).copied();
            print_settings(settings, strategy);
            Ok(())
        }
        "set" => handle_settings_set(&args[1..], settings),
        "reset" => {
            let strategy_id = args
                .get(1)
                .copied()
                .ok_or("Usage: settings reset <strategy>")?;
            if find_strategy_spec(strategy_id).is_none() {
                return Err(format!("Unknown strategy: {strategy_id}").into());
            }
            settings.reset_strategy_params(strategy_id);
            let path = save_settings(settings)?;
            println!("Reset {strategy_id} defaults and saved to {}", path.display());
            Ok(())
        }
        "save" => {
            let path = save_settings(settings)?;
            println!("Saved settings to {}", path.display());
            Ok(())
        }
        "help" | "h" | "?" => {
            print_backtest_help();
            Ok(())
        }
        _ => Err("Usage: settings show [strategy] | settings set ... | settings reset <strategy> | settings save".into()),
    }
}

fn handle_settings_set(args: &[&str], settings: &mut AppSettings) -> Result<(), Box<dyn Error>> {
    if args.len() < 3 {
        return Err("Usage: settings set global symbol <code> | settings set global initial-capital <n> | settings set <strategy> <param> <value>".into());
    }

    if args[0] == "global" {
        if args[1] == "symbol" {
            settings.default_symbol = args[2].to_string();
            let path = save_settings(settings)?;
            println!("Updated global symbol and saved to {}", path.display());
            return Ok(());
        }

        if args[1] == "initial-capital" {
            let value = args[2].parse::<f64>()?;
            if value <= 0.0 {
                return Err("initial-capital must be > 0".into());
            }
            settings.default_initial_capital = value;
            let path = save_settings(settings)?;
            println!("Updated initial capital and saved to {}", path.display());
            return Ok(());
        }

        return Err(
            "Usage: settings set global symbol <code> | settings set global initial-capital <n>"
                .into(),
        );
    }

    if args.len() < 3 {
        return Err("Usage: settings set <strategy> <param> <value>".into());
    }

    let strategy_id = args[0];
    let param = args[1];
    let value = args[2].parse::<f64>()?;
    settings
        .set_strategy_param(strategy_id, param, value)
        .map_err(|err| -> Box<dyn Error> { err.into() })?;

    let path = save_settings(settings)?;
    println!(
        "Updated {}.{}={} and saved to {}",
        strategy_id,
        param,
        value,
        path.display()
    );

    Ok(())
}

fn print_settings(settings: &AppSettings, strategy_filter: Option<&str>) {
    println!("Global settings:");
    println!("  symbol: {}", settings.default_symbol);
    println!("  initial-capital: {:.2}", settings.default_initial_capital);

    println!("Strategy defaults:");
    for spec in strategy_specs() {
        if let Some(filter) = strategy_filter {
            if filter != spec.id {
                continue;
            }
        }

        let values: HashMap<String, f64> = settings.strategy_values(spec.id);
        println!("  {}:", spec.id);
        if spec.params.is_empty() {
            println!("    (no params)");
            continue;
        }

        for param in spec.params {
            let value = values.get(param.name).copied().unwrap_or(0.0);
            println!("    {} = {}", param.name, value);
        }
    }
}
