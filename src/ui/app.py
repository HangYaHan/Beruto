from __future__ import annotations

import sys
from typing import Optional
from PyQt6 import QtWidgets

try:
    import qdarktheme
except Exception:  # pragma: no cover
    qdarktheme = None

from src.ui.views.main_window import MainWindow


def run_ui(default_task: Optional[str] = None) -> int:
    """Launch the Qt UI. Returns an exit code."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    if qdarktheme:
        qdarktheme.setup_theme(custom_colors={"primary": "#27c2d7"})
    window = MainWindow(default_task=default_task)
    window.show()
    return app.exec()


__all__ = ["run_ui"]
