mod backtest;
mod data;
mod strategy;

use backtest::engine::run_backtest;
use backtest::result::BacktestResult;
use data::data_source::load_daily_quotes;
use strategy::base::Strategy;
use strategy::contrarian::{BuyAndHoldStrategy, ContrarianStrategy};
use std::process;

fn print_summary(strategy_name: &str, result: &BacktestResult) {
    println!("Strategy: {}", strategy_name);
    println!("Initial capital: {:.2}", result.initial_capital);
    println!("Final equity:    {:.2}", result.final_equity);
    println!("Total return:    {:.2}%", result.total_return_pct);
    println!("Max drawdown:    {:.2}%", result.max_drawdown_pct);
    println!("Trades:          {}", result.trades);
    println!("Equity points:   {}", result.equity_curve.len());
}

fn print_compact_row(label: &str, result: &BacktestResult) {
    println!(
        "{:<34} return={:>7.2}%  mdd={:>6.2}%  trades={:>4}",
        label, result.total_return_pct, result.max_drawdown_pct, result.trades
    );
}

fn main() {
    let file_path = "data/159581_daily.csv";

    let quotes = match load_daily_quotes(file_path) {
        Ok(data) => data,
        Err(err) => {
            eprintln!("Failed to load {}: {}", file_path, err);
            process::exit(1);
        }
    };

    if quotes.is_empty() {
        println!("No rows found in {}", file_path);
        return;
    }

    let first = &quotes[0];
    let last = &quotes[quotes.len() - 1];

    println!("Loaded 159581 daily data from {}", file_path);
    println!("Rows: {}", quotes.len());
    println!("Start: {} close={:.3}", first.date, first.close);
    println!("End:   {} close={:.3}", last.date, last.close);

    let initial_capital = 100_000.0;

    let mut buy_and_hold = BuyAndHoldStrategy::new();
    let buy_and_hold_result = run_backtest(&mut buy_and_hold, &quotes, initial_capital);

    println!();
    print_summary(buy_and_hold.name(), &buy_and_hold_result);

    let mut contrarian = ContrarianStrategy::new();
    let contrarian_result = run_backtest(&mut contrarian, &quotes, initial_capital);

    println!();
    print_summary(contrarian.name(), &contrarian_result);

    println!();
    println!("Contrarian threshold sweep (159581):");
    let sweep = [(-0.5, 0.5), (-1.0, 1.0), (-1.5, 1.5)];

    for (buy_drop, sell_rise) in sweep {
        let mut strategy = ContrarianStrategy::with_thresholds(buy_drop, sell_rise);
        let result = run_backtest(&mut strategy, &quotes, initial_capital);
        let (d, r) = strategy.thresholds();
        let label = format!("Contrarian(drop<= {d:.1}%, rise>= {r:.1}%)");
        print_compact_row(&label, &result);
    }
}
