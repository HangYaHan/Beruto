from __future__ import annotations

from typing import Callable, Dict

HELP_TEXT = """FeedbackTrader interactive CLI
Commands:
    help, h, ?       Show this help
    echo <text>      Echo the provided text
    exit, quit, q    Exit the CLI

Backtest / plot commands are removed while the engine and data interfaces are being redesigned.
"""

def print_help() -> None:
    """Print help text to stdout."""
    print(HELP_TEXT)

def execute_command(cmd_line: str, write: Callable[[str], None]) -> Dict[str, object] | None:
    """Execute a single CLI command and return a result dict for UI.

    Returns:
      {"type": "text", "content": str}
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
        return interactive_loop()
    except Exception as e:
        return 2

if __name__ == "__main__":
    raise SystemExit(main())