"""
Main entry for the application.
Defines the CLI / startup flow entrypoint.
"""
from typing import Any
import sys
import argparse
from pathlib import Path

def main(args: Any = None) -> int:
    """
    Application main entry point.
    - ensure project root is on sys.path when executed directly
    - defaults to launching the PyQt UI
    - optional flag --cli keeps the legacy CLI available
    Returns an exit code (int).
    """
    # When executed directly (python src/main.py), make sure project root is importable
    if __package__ is None: 
        project_root = Path(__file__).resolve().parents[1]  # Get father directory of 'src'
        sys.path.insert(0, str(project_root))

    parser = argparse.ArgumentParser(description="Beruto application entrypoint")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of UI")
    parser.add_argument("--task", help="Preselect strategy plan for UI run", default=None)
    parsed = parser.parse_args(args)

    if parsed.cli:
        from src.system.CLI import main as cli_main
        return cli_main([])

    try:
        from src.ui.app import run_ui
        return run_ui(default_task=parsed.task)
    except Exception as exc:
        print("UI failed to start, falling back to CLI. Error:", exc)
        from src.system.CLI import main as cli_main
        return cli_main([])


if __name__ == "__main__":
    raise SystemExit(main())