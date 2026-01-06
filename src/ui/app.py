from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
from PyQt6 import QtWidgets, QtGui


def _set_windows_app_id(app_id: str) -> None:
    """Set Windows AppUserModelID so taskbar uses our icon instead of python.exe."""
    if sys.platform.startswith("win"):
        try:
            import ctypes  # type: ignore

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)  # type: ignore[attr-defined]
        except Exception:
            pass

from src.ui.views.main_window import MainWindow


def run_ui(default_task: Optional[str] = None) -> int:
    """Launch the Qt UI. Returns an exit code."""
    _set_windows_app_id("Beruto.App")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    icon_base = Path(__file__).resolve().with_name("icon")
    icon_path = None
    for ext in (".ico", ".png"):
        candidate = icon_base.with_suffix(ext)
        if candidate.exists():
            icon_path = candidate
            break
    if icon_path:
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    window = MainWindow(default_task=default_task)
    window.show()
    return app.exec()


__all__ = ["run_ui"]
