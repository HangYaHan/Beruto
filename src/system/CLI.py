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
    backtest, bt     Run a backtest
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
    from src.backtest.engine import run_task
    if not args:
        write("Usage: backtest TASK_NAME (without .json, from tasks folder)")
        return {"type": "text", "content": "缺少参数：TASK_NAME"}
    task_name = args[0]
    try:
        curve = run_task(task_name)
        final = curve.iloc[-1]
        write("Backtest done.")
        write(f"  Final equity: {final['equity']:.2f}")
        write(f"  Cash: {final['cash']:.2f}")
        write(f"  Position value: {final['position_value']:.2f}")
        write(f"  Stock return (pct change of position value): {final['stock_return_pct']*100:.2f}%")
        # Heuristically find latest run dir; show equity plot if present
        from pathlib import Path
        result_root = Path(__file__).resolve().parents[2] / 'result'
        latest_dir: Optional[Path] = None
        if result_root.exists():
            dirs = [p for p in result_root.iterdir() if p.is_dir()]
            if dirs:
                latest_dir = max(dirs, key=lambda p: p.stat().st_mtime)
        images = []
        if latest_dir:
            for name in ("equity_plot.png", "equity_baselines.png"):
                p = latest_dir / name
                if p.exists():
                    images.append(str(p))
        return {"type": "images" if len(images) > 1 else ("image" if images else "text"),
                "paths": images, "path": images[0] if images else "",
                "content": "Backtest finished."}
    except Exception as e:
        logger.exception("Backtest failed: %s", e)
        write(f"Backtest failed: {e}")
        return {"type": "text", "content": f"Backtest failed: {e}"}


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