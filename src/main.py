"""
Main entry for the application.
Defines the CLI / startup flow entrypoint.
"""
from typing import Any
import sys
from pathlib import Path
from system.log import get_logger
from system.startup import ensure_workspace_dirs

logger = get_logger(__name__)

def main(args: Any = None) -> int:
    """
    Application main entry point.
    - ensure project root is on sys.path when executed directly
    - delegate to the interactive/argparse CLI implemented in src.system.CLI
    Returns an exit code (int).
    """
    # When executed directly (python src/main.py), make sure project root is importable
    if __package__ is None:
        project_root = Path(__file__).resolve().parents[1] # Get father directory of 'src'
        sys.path.insert(0, str(project_root))

    # Import CLI entrypoint and delegate
    from src.system.CLI import main as cli_main
    # Ensure workspace directories once at app start (redundant-safe with CLI)
    ensure_workspace_dirs()
    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())