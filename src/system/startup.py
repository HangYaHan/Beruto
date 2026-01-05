from __future__ import annotations

from pathlib import Path
from typing import Iterable
from .log import get_logger

logger = get_logger(__name__)

REQUIRED_DIRS = ("tasks", "strategies", "data", "logs", "result")

def ensure_workspace_dirs(root: Path | None = None, extra_dirs: Iterable[str] | None = None) -> None:
    """Ensure required workspace directories exist under project root.

    If a directory is missing, create it.
    - root: project root path; if None, infer from this file's location.
    - extra_dirs: additional folder names to ensure.
    """
    if root is None:
        root = Path(__file__).resolve().parents[2]
    dirs = list(REQUIRED_DIRS)
    if extra_dirs:
        dirs.extend(list(extra_dirs))
    for name in dirs:
        p = root / name
        try:
            p.mkdir(parents=True, exist_ok=True)
            logger.info("Workspace check: ensured directory %s", p)
        except Exception as e:
            logger.exception("Failed to ensure directory %s: %s", p, e)

__all__ = ["ensure_workspace_dirs", "REQUIRED_DIRS"]

def new_result_run_dir(root: Path | None = None) -> Path:
    """Create a timestamped subdirectory under result and return its path.

    Format: YYYYMMDD_HH_MM
    """
    if root is None:
        root = Path(__file__).resolve().parents[2]
    result_root = root / "result"
    result_root.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H_%M")
    run_dir = result_root / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Result run directory created: %s", run_dir)
    return run_dir

