from __future__ import annotations

from typing import List
from PyQt6 import QtCore, QtGui, QtWidgets

from src.system.CLI import execute_command


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_task: str | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.default_task = default_task
        self.command_history: list[str] = []
        self.history_index: int | None = None
        self.setWindowTitle("Beruto")
        self.resize(1920, 1080)
        self._build_layout()

    def _build_layout(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)

        self.left_panel = self._build_left_tabs()
        self.middle_panel = self._build_chart_placeholder()
        self.right_panel = self._build_info_wall()

        top_row.addWidget(self.left_panel, stretch=1)
        top_row.addWidget(self.middle_panel, stretch=3)
        top_row.addWidget(self.right_panel, stretch=1)

        self.console = self._build_console()

        outer.addLayout(top_row, stretch=4)
        outer.addWidget(self.console, stretch=1)

    def _build_left_tabs(self) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QFrame()
        layout = QtWidgets.QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._task_table(), "All Tasks")
        for symbol in ["SZ000001", "SH600519", "SZ300750"]:
            tabs.addTab(self._task_table(filter_symbol=symbol), symbol)

        layout.addWidget(tabs)
        return wrapper

    def _task_table(self, filter_symbol: str | None = None) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(widget)
        table = QtWidgets.QTableWidget()
        headers = ["Symbol", "Strategy", "Status", "Progress", "ETA"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setShowGrid(True)
        table.setAlternatingRowColors(True)
        sample_rows = self._sample_tasks()
        rows: List[List[str]] = []
        for row in sample_rows:
            if filter_symbol and row[0] != filter_symbol:
                continue
            rows.append(row)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(value)
                if value in {"Running", "Done", "Failed"}:
                    color = {"Running": "#27c2d7", "Done": "#2ecc71", "Failed": "#e74c3c"}.get(value, "#d8d8d8")
                    item.setForeground(QtGui.QBrush(QtGui.QColor(color)))
                table.setItem(r, c, item)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        vbox.addWidget(table)
        return widget

    def _build_chart_placeholder(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)
        title = QtWidgets.QLabel("Chart Area (1920x1080 layout placeholder)")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; color: #dddddd")
        vbox.addWidget(title, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        return frame

    def _build_info_wall(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(8)
        header = QtWidgets.QLabel("Info Wall")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        vbox.addWidget(header)
        placeholder = QtWidgets.QLabel("Metrics / Positions / Task Queue")
        placeholder.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        placeholder.setWordWrap(True)
        vbox.addWidget(placeholder, stretch=1)
        return frame

    def _build_console(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QFrame()
        panel.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlainText("Console ready. Type commands below.")

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Enter command...")
        self.input.installEventFilter(self)

        layout.addWidget(self.log_view, stretch=3)
        layout.addWidget(self.input)

        self.input.returnPressed.connect(self._handle_submit)
        return panel

    def _handle_submit(self) -> None:
        cmd = self.input.text().strip()
        if not cmd:
            return
        self._append_log(f"$ {cmd}")
        self.command_history.append(cmd)
        self.history_index = None
        self.input.clear()
        try:
            res = execute_command(cmd, write=self._append_log)
            if res:
                if res.get("type") in {"image", "images"}:
                    paths = res.get("paths") or [res.get("path")]
                    if paths:
                        self._append_log("Output files:")
                        for p in paths:
                            self._append_log(f"  {p}")
        except Exception as exc:  # safety guard
            self._append_log(f"Command error: {exc}")

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802 (Qt override)
        if obj is self.input and event.type() == QtCore.QEvent.Type.KeyPress:
            key_event = event  # type: ignore[assignment]
            if key_event.key() == QtCore.Qt.Key.Key_Up:
                self._recall_history(direction=-1)
                return True
            if key_event.key() == QtCore.Qt.Key.Key_Down:
                self._recall_history(direction=1)
                return True
        return super().eventFilter(obj, event)

    def _recall_history(self, direction: int) -> None:
        if not self.command_history:
            return
        if self.history_index is None:
            self.history_index = len(self.command_history)
        self.history_index = max(0, min(len(self.command_history) - 1, self.history_index + direction))
        self.input.setText(self.command_history[self.history_index])

    def _append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)

    def _sample_tasks(self) -> List[List[str]]:
        return [
            ["SZ000001", "Grid Search", "Running", "42%", "02:10"],
            ["SH600519", "ML Sweep", "Done", "100%", "--"],
            ["SZ300750", "Baseline", "Failed", "68%", "--"],
            ["SZ000001", "SMA-20/60", "Done", "100%", "--"],
        ]
