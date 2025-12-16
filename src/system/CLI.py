from __future__ import annotations

import sys
import shutil
from pathlib import Path
from typing import NoReturn

from .log import get_logger
from .startup import ensure_workspace_dirs
from .help_texts import get_help_text

logger = get_logger(__name__)

HELP_TEXT = get_help_text()  # Backward-compatible general help text

ROOT_DIR = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT_DIR / "result"
LOG_DIR = ROOT_DIR / "logs"


def _delete_path(p: Path) -> None:
    """Delete file or directory recursively, ignoring missing."""
    if not p.exists():
        return
    if p.is_dir():
        # Be resilient: ignore permission issues and continue
        try:
            shutil.rmtree(p, ignore_errors=True)
        except Exception as e:
            logger.warning("Failed to delete directory %s: %s", p, e)
    else:
        # Windows may forbid unlinking files opened by the logger.
        # Catch and ignore such errors to avoid crashing the CLI.
        try:
            p.unlink(missing_ok=True)  # type: ignore[arg-type]
        except TypeError:
            # Python <3.8 compat; fall back
            try:
                p.unlink()
            except FileNotFoundError:
                pass
            except PermissionError as e:
                logger.info("Skipping in-use file %s: %s", p, e)
            except Exception as e:
                logger.warning("Failed to delete file %s: %s", p, e)
        except PermissionError as e:
            logger.info("Skipping in-use file %s: %s", p, e)
        except Exception as e:
            logger.warning("Failed to delete file %s: %s", p, e)


def handle_remove(args: list[str]) -> None:
    """Handle remove/rm command with required flags."""
    if not args:
        print(get_help_text("remove"))
        return

    flag = args[0].lower()
    if flag not in {"-r", "-l", "-all"}:
        if flag == "-?":
            print(get_help_text("remove"))
            return
        print(get_help_text("remove"))
        return

    # ensure dirs exist
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if flag == "-r":
        if len(args) == 2 and args[1].lower() == "leaderboard":
            lb = RESULT_DIR / "leaderboard.csv"
            if lb.exists():
                _delete_path(lb)
                logger.info("Deleted leaderboard at %s", lb)
                print("Deleted leaderboard.")
            else:
                print("Leaderboard not found; nothing to delete.")
            return
			
        # clear result contents except leaderboard
        for item in RESULT_DIR.iterdir():
            if item.name == "leaderboard.csv":
                continue
            _delete_path(item)
        logger.info("Cleared result folder (kept leaderboard)")
        print("Cleared result outputs (leaderboard kept).")
        return

    if flag == "-l":
        for item in LOG_DIR.iterdir():
            _delete_path(item)
        logger.info("Cleared all old logs")
        print("Cleared all old logs.")
        return

    if flag == "-all":
        for item in RESULT_DIR.iterdir():
            if item.name == "leaderboard.csv":
                continue
            _delete_path(item)
        for item in LOG_DIR.iterdir():
            _delete_path(item)
        logger.info("Cleared result (kept leaderboard) and logs")
        print("Cleared result outputs (leaderboard kept) and logs.")
        return

def print_help() -> None:
    """Print help text to stdout."""
    print(get_help_text())

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
                print(get_help_text("backtest"))
                continue
            if args and args[0] == "-?":
                print(get_help_text("backtest"))
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
            if args and args[0] == "-?":
                print(get_help_text("config"))
            else:
                print("Config command is not implemented yet. Use 'config -?' for intended usage.")
            continue

        if cmd in ("plot", "pt"):
            from src.ploter.ploter import run_plot_command
            if args and args[0] == "-?":
                print(get_help_text("plot"))
                continue
            run_plot_command(args)
            continue

        if cmd in ("remove", "rm"):
            if args and args[0] == "-?":
                print(get_help_text("remove"))
                continue
            handle_remove(args)
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