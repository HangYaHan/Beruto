from __future__ import annotations

import sys
from typing import NoReturn

from .log import get_logger
from src.backtest.engine import BacktestEngine

logger = get_logger(__name__)

HELP_TEXT = """FeedbackTrader interactive CLI
Commands:
    help, h, ?       Show this help
    config, cfg      Show or set configuration
    backtest, bt     Run a backtest
    plot             Plot cached OHLC data
    exit, quit, q    Exit the CLI

Plot usage:
    plot SYMBOL [-start YYYYMMDD] [-end YYYYMMDD]
             [-frame daily|weekly] [-source akshare|yfinance|csv]
             [-refresh] [-output path.png] [-ma 5,20]

Examples:
    plot sh600000 -start 20240101 -end 20241130 -source akshare
    plot AAPL -start 2024-01-01 -frame weekly -output aapl_weekly.png -ma 5,20
"""

def print_help() -> None:
    """Print help text to stdout."""
    print(HELP_TEXT)

def interactive_loop() -> int:
    """Simple REPL that responds to exact commands like 'help' and 'exit'."""
    print("FeedbackTrader CLI. Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("Beruto > ")
        except (KeyboardInterrupt, EOFError):
            print()  # newline on ^C / EOF
            return 0

        cmd_line = line.strip()
        if not cmd_line:
            continue

        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # strict/exact matching on the command token
        if cmd in ("help", "h", "?"):
            logger.info("User requested help")
            print_help()
            continue

        if cmd in ("exit", "quit", "q"):
            logger.info("User requested exit")
            print("Bye.")
            return 0
        
        if cmd in ("backtest", "bt"):
            logger.info("User requested backtest command (not implemented)")
            print("Backtest command is not implemented yet.")
            backtest_engine = BacktestEngine()
            backtest_engine.run_backtest()
            continue

        if cmd in ("config", "cfg"):
            logger.info("User requested config command (not implemented)")
            print("Config command is not implemented yet.")
            continue

        if cmd == "anjzy":
            logger.info("User entered secret command 'anjzy'")
            print("You found the secret command! -- ashgk")
            continue
        
        if cmd == "axhxt":
            logger.info("User entered secret command 'axhxt'")
            print("You found the top secret command! -- amhxr")
            continue

        if cmd == "plot":
            from src.ploter.ploter import run_plot_command
            run_plot_command(args)
            continue

        if cmd == "plot":
            from src.ploter.ploter import run_plot_command
            run_plot_command(args)
            continue

        print(f"Unknown command: {cmd_line}. Type 'help' for available commands.")

def main(argv: list[str] | None = None) -> int:
    """Entry point for the interactive CLI."""
    try:
        return interactive_loop()
    except Exception as e:
        logger.exception("CLI failed: %s", e)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())