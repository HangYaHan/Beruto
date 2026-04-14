mod help;
mod parser;

use crate::backtest::engine::run_backtest_for_symbol;
use crate::backtest::result::BacktestResult;
use crate::backtest::visualize::write_visualization_html;
use crate::data::data_source::{load_daily_quotes_by_symbol, symbol_to_daily_csv_path};
use crate::data::fetcher::fetch_and_store_daily_quotes;
use crate::data::settings::{load_settings, save_settings, settings_path, AppSettings};
use crate::data::storage::{
    clean_results, ensure_results_dir, load_all_run_records, make_run_id, results_dir,
    save_run_record, BacktestRunRecord,
};
use crate::strategy::{build_strategy, find_strategy_spec, strategy_specs, StrategyConfig};
use help::{print_banner, print_help, print_startup_help};
use parser::{
    parse_f64_list_flag, parse_flag_value, parse_list_flag, parse_usize_flag,
    parse_usize_list_flag,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fs;
use std::io::{self, Error as IoError, ErrorKind, Write};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

pub fn run_repl() -> Result<(), Box<dyn Error>> {
    print_banner();
    print_startup_help();

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

include!("core_commands.rs");
include!("run_planning.rs");
include!("backtest_flow.rs");
include!("backtest_reporting.rs");
include!("visualization_and_clean.rs");
