from __future__ import annotations

import sys
from typing import Callable, Dict, Optional

from .log import get_logger
from .startup import ensure_workspace_dirs

logger = get_logger(__name__)

HELP_TEXT = """FeedbackTrader interactive CLI
Commands:
    help, h, ?       Show this help
    config, cfg      Show or set configuration
    backtest, bt     Load a strategy plan (preview only)
    plot, pt         Plot cached OHLC data
    remove, rm       Clean everything (results, cache, logs)
    exit, quit, q    Exit the CLI

For detailed all command usage, see docs/COMMANDS.md

If you just want to see something quick, try:
    plot sh600000 --frame weekly
"""

def print_help() -> None:
    """Print help text to stdout."""
    print(HELP_TEXT)

def _exec_backtest(args: list[str], write: Callable[[str], None]) -> Dict[str, object]:
    from src.backtest.engine import run_task, summarize_plan
    if not args:
        write("Usage: backtest PLAN_NAME (from strategies folder, without .json)")
        return {"type": "text", "content": "缺少参数：PLAN_NAME"}
    plan_name = args[0]
    try:
        plan = run_task(plan_name)
        summary = summarize_plan(plan)
        write(f"Plan loaded: {summary['name']}")
        write(f"Symbols: {', '.join(summary['symbols']) or '(none)'}")
        if summary.get("factors"):
            for f in summary["factors"]:
                write(f"  - {f['name']}: {f['module']}.{f['class']} -> {', '.join(f['symbols'])}")
                if f.get("params"):
                    write(f"    params: {f['params']}")
        return {"type": "text", "content": f"Plan {summary['name']} loaded ({len(summary['factors'])} factors)."}
    except Exception as e:
        logger.exception("Plan load failed: %s", e)
        write(f"Plan load failed: {e}")
        return {"type": "text", "content": f"Plan load failed: {e}"}


def _exec_plot(args: list[str], write: Callable[[str], None]) -> Dict[str, object]:
    from src.ploter.ploter import run_plot_command
    try:
        out_path = run_plot_command(args)
        if out_path:
            write("Plot done.")
            return {"type": "image", "path": out_path}
        return {"type": "text", "content": "Plot finished (no output path returned)."}
    except Exception as e:
        logger.exception("Plot failed: %s", e)
        write(f"Plot failed: {e}")
        return {"type": "text", "content": f"Plot failed: {e}"}


def execute_command(cmd_line: str, write: Callable[[str], None]) -> Dict[str, object] | None:
    """Execute a single CLI command and return a result dict for UI.

    Returns one of:
      {"type": "text", "content": str}
      {"type": "image", "path": str}
      {"type": "images", "paths": list[str]}
    """
    line = cmd_line.strip()
    if not line:
        return None
    parts = line.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in ("help", "h", "?"):
        write(HELP_TEXT)
        return {"type": "text", "content": HELP_TEXT}
    if cmd in ("exit", "quit", "q"):
        write("Bye.")
        return {"type": "text", "content": "Bye."}
    if cmd in ("backtest", "bt"):
        return _exec_backtest(args, write)
    if cmd in ("plot", "pt"):
        return _exec_plot(args, write)
    if cmd in ("config", "cfg"):
        write("Config command is not implemented yet.")
        return {"type": "text", "content": "Config command is not implemented yet."}
    if cmd == "echo":
        text = " ".join(args) if args else ""
        write(text)
        return {"type": "text", "content": text}
    if cmd == "anjzy":
        write("You found the secret command! -- ashgk")
        return {"type": "text", "content": "You found the secret command! -- ashgk"}
    if cmd == "axhxt":
        write("You found the top secret command! -- amhxr")
        return {"type": "text", "content": "You found the top secret command! -- amhxr"}

    write(f"Unknown command: {line}. Type 'help' for available commands.")
    return {"type": "text", "content": f"Unknown command: {line}"}


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

        # Delegate to single-command executor
        res = execute_command(cmd_line, write=lambda s: print(s))
        if res and res.get("content") == "Bye.":
            return 0

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