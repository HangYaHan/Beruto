from __future__ import annotations

from typing import Callable

from PyQt6 import QtCore, QtGui, QtWidgets


class HistoryLineEdit(QtWidgets.QLineEdit):
    def __init__(self, recall_history: Callable[[int], None], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._recall_history = recall_history

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Up:
            self._recall_history(-1)
            event.accept()
            return
        if event.key() == QtCore.Qt.Key.Key_Down:
            self._recall_history(1)
            event.accept()
            return
        super().keyPressEvent(event)


class ConsolePanel(QtWidgets.QFrame):
    def __init__(self, on_command: Callable[[str], None], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_command = on_command
        self.command_history: list[str] = []
        self.history_index: int | None = None
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlainText("Console ready. Type commands below.")

        self.input = HistoryLineEdit(self._recall_history)
        self.input.setPlaceholderText("Enter command...")

        layout.addWidget(self.log_view, stretch=3)
        layout.addWidget(self.input)

        self.input.returnPressed.connect(self._handle_submit)

    def _handle_submit(self) -> None:
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.append_log(f"$ {cmd}")
        self.command_history.append(cmd)
        self.history_index = None
        self.input.clear()
        self._on_command(cmd)

    def _recall_history(self, direction: int) -> None:
        if not self.command_history:
            return
        if self.history_index is None:
            self.history_index = len(self.command_history)
        self.history_index = max(0, min(len(self.command_history) - 1, self.history_index + direction))
        self.input.setText(self.command_history[self.history_index])

    def append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)


__all__ = ["ConsolePanel", "HistoryLineEdit"]
