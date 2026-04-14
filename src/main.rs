mod backtest;
mod cli;
mod data;
mod manager;
mod portfolio;
mod strategy;

use std::process;

fn main() {
    if let Err(err) = cli::run_repl() {
        eprintln!("CLI failed: {}", err);
        process::exit(1);
    }
}
