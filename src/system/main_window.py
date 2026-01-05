"""Compatibility shim for legacy imports.

The main window has moved to src.ui.views.main_window; this module keeps
any older import paths working until callers are updated.
"""

from src.ui.views.main_window import MainWindow

__all__ = ["MainWindow"]
