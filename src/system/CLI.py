from __future__ import annotations

import sys
from typing import NoReturn

from .log import get_logger
from .startup import ensure_workspace_dirs

logger = get_logger(__name__)

HELP_TEXT = """FeedbackTrader interactive CLI
Commands:
    help, h, ?       Show this help
    config, cfg      Show or set configuration
    backtest, bt     Run a backtest
    plot, pt         Plot cached OHLC data
    exit, quit, q    Exit the CLI

For detailed all command usage, see docs/COMMANDS.md

If you just want to see something quick, try:
    plot sh600000 --frame weekly
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
            from src.backtest.engine import run_task
            if not args:
                print("Usage: backtest TASK_NAME (without .json, from tasks folder)")
                continue
            task_name = args[0]
            try:
                curve = run_task(task_name)
                final = curve.iloc[-1]
                print(f"Backtest done.")
                print(f"  Final equity: {final['equity']:.2f}")
                print(f"  Cash: {final['cash']:.2f}")
                print(f"  Position value: {final['position_value']:.2f}")
                print(f"  Stock return (pct change of position value): {final['stock_return_pct']*100:.2f}%")
            except Exception as e:
                logger.exception("Backtest failed: %s", e)
                print(f"Backtest failed: {e}")
            continue

        if cmd in ("config", "cfg"):
            logger.info("User requested config command (not implemented)")
            print("Config command is not implemented yet.")
            continue

        if cmd in ("plot", "pt"):
            from src.ploter.ploter import run_plot_command
            run_plot_command(args)
            continue

        if cmd == "anjzy":
            logger.info("User entered secret command 'anjzy'")
            print("You found the secret command! -- ashgk")
            continue
        
        if cmd == "axhxt":
            logger.info("User entered secret command 'axhxt'")
            print("You found the top secret command! -- amhxr")
            continue

        print(f"Unknown command: {cmd_line}. Type 'help' for available commands.")

def main(argv: list[str] | None = None) -> int:
    """Entry point for the interactive CLI."""
    try:
        # Ensure required directories before starting CLI loop
        ensure_workspace_dirs()
        return interactive_loop()
    except Exception as e:
        logger.exception("CLI failed: %s", e)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())