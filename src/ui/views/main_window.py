from __future__ import annotations

from pathlib import Path
from typing import Dict

import akshare as ak
import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets

from src.system.CLI import execute_command


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_task: str | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.default_task = default_task
        self.command_history: list[str] = []
        self.history_index: int | None = None
        self.setWindowTitle("Beruto")
        icon_path = Path(__file__).resolve().parents[2] / "ui" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        self.resize(1920, 1080)
        self.move(0, 0)
        self._tooltip_delay_ms = 350  # shorten tooltip hover delay (~half default)
        self._tooltip_targets: Dict[QtWidgets.QWidget, str] = {}
        # Set early to avoid AttributeError when eventFilter is triggered before console creation.
        self.input: QtWidgets.QLineEdit | None = None
        self.symbol_map: Dict[str, str] = self._load_symbol_cache()
        self.name_to_code: Dict[str, str] = {name: code for code, name in self.symbol_map.items()}
        self.suggestion_list = [f"{code} {name}" for code, name in self.symbol_map.items()]
        self.completer_model = QtCore.QStringListModel(self.suggestion_list)
        self._build_menu()
        self._build_layout()

    def _build_layout(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(8, 0, 8, 8)
        outer.setSpacing(4)

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

    def _build_menu(self) -> None:
        bar = self.menuBar()
        bar.setStyleSheet(
            "QMenuBar { padding: 0px; margin: 0px; spacing: 0px; border: 0px; border-radius: 0px; background: transparent; }"
            "QMenuBar::item { padding: 4px 8px; margin: 0px; border: 0px; border-radius: 0px; }"
            "QMenu::icon { padding: 0px; margin: 0px; width: 0px; }"
            "QMenu::item { padding: 6px 18px; margin: 2px 6px; min-width: 114px; }"
            "QMenu::item:selected { background: palette(Highlight); color: palette(HighlightedText); }"
        )

        file_menu = bar.addMenu("File")
        new_action = QtGui.QAction("New Strategy", self)
        new_action.triggered.connect(self._new_strategy)
        open_action = QtGui.QAction("Open Strategy", self)
        open_action.triggered.connect(self._open_strategy)
        save_action = QtGui.QAction("Save Strategy", self)
        save_action.triggered.connect(self._save_strategy)
        close_action = QtGui.QAction("Close Strategy", self)
        close_action.triggered.connect(self._close_strategy)
        exit_action = QtGui.QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(close_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        help_menu = bar.addMenu("Help")
        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _build_left_tabs(self) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QFrame()
        layout = QtWidgets.QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        tabs = QtWidgets.QTabWidget()
        self.symbol_list_widget = QtWidgets.QListWidget()
        self.symbol_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.factor_list_widget = QtWidgets.QListWidget()
        self.factor_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        tabs.addTab(self._build_symbols_tab(), "Symbols")
        tabs.addTab(self._build_factors_tab(), "Factors")

        layout.addWidget(tabs)
        layout.addWidget(self._build_action_buttons())
        return wrapper

    def _build_action_buttons(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(bar)
        hbox.setContentsMargins(0, 6, 0, 0)
        hbox.setSpacing(2)
        hbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        buttons = [
            ("Add Symbol", "Add symbol to list", self._make_colored_icon("add", "#2ecc71")),
            ("Delete Symbol", "Delete selected symbols", self._make_colored_icon("remove", "#e74c3c")),
            ("Run", "Run current strategy", self._make_colored_icon("run", "#f1c40f")),
        ]
        hbox.addStretch(1)
        for text, tooltip, icon in buttons:
            btn = QtWidgets.QToolButton()
            btn.setIcon(icon)
            btn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
            self._register_tooltip_target(btn, tooltip)
            btn.setAutoRaise(True)
            btn.setIconSize(QtCore.QSize(26, 26))
            if text == "Add Symbol":
                btn.clicked.connect(self._on_add_symbol)
            elif text == "Delete Symbol":
                btn.clicked.connect(self._on_delete_symbol)
            hbox.addWidget(btn)

        hbox.addStretch(1)
        return bar

    def _make_colored_icon(self, kind: str, color: str) -> QtGui.QIcon:
        """Create a simple colored icon for add/remove/run without external assets."""
        size = 30
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(color))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(color)))

        center = size // 2
        offset = 9
        if kind == "add":
            painter.drawLine(center, offset, center, size - offset)
            painter.drawLine(offset, center, size - offset, center)
        elif kind == "remove":
            painter.drawLine(offset, center, size - offset, center)
        elif kind == "run":
            points = [
                QtCore.QPoint(offset, offset),
                QtCore.QPoint(size - offset, center),
                QtCore.QPoint(offset, size - offset),
            ]
            painter.drawPolygon(QtGui.QPolygon(points))
        painter.end()

        return QtGui.QIcon(pixmap)

    def _build_symbols_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        label = QtWidgets.QLabel("Symbols")
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        vbox.addWidget(label)

        vbox.addWidget(self.symbol_list_widget)
        return widget

    def _build_factors_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        label = QtWidgets.QLabel("Factors")
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        vbox.addWidget(label)

        self.factor_list_widget.clear()
        vbox.addWidget(self.factor_list_widget)

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
        if obj in self._tooltip_targets:
            if event.type() == QtCore.QEvent.Type.Enter:
                QtCore.QTimer.singleShot(
                    self._tooltip_delay_ms, lambda w=obj: self._show_tooltip_if_hovered(w)
                )
            elif event.type() == QtCore.QEvent.Type.Leave:
                QtWidgets.QToolTip.hideText()

        if self.input is not None and obj is self.input and event.type() == QtCore.QEvent.Type.KeyPress:
            key_event = event  # type: ignore[assignment]
            if key_event.key() == QtCore.Qt.Key.Key_Up:
                self._recall_history(direction=-1)
                return True
            if key_event.key() == QtCore.Qt.Key.Key_Down:
                self._recall_history(direction=1)
                return True
        return super().eventFilter(obj, event)

    def _register_tooltip_target(self, widget: QtWidgets.QWidget, text: str) -> None:
        self._tooltip_targets[widget] = text
        widget.setToolTip(text)
        widget.installEventFilter(self)

    def _show_tooltip_if_hovered(self, widget: QtCore.QObject) -> None:
        if isinstance(widget, QtWidgets.QWidget) and widget.underMouse():
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), widget.toolTip(), widget)

    def _recall_history(self, direction: int) -> None:
        if not self.command_history:
            return
        if self.history_index is None:
            self.history_index = len(self.command_history)
        self.history_index = max(0, min(len(self.command_history) - 1, self.history_index + direction))
        self.input.setText(self.command_history[self.history_index])

    def _append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)

    def _show_about_dialog(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "\nThis is the GUI version of Beruto.\n",
        )

    # --- Strategy menu handlers ---
    def _new_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "New Strategy", "TODO: create a new strategy.")

    def _open_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "Open Strategy", "TODO: open an existing strategy.")

    def _save_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "Save Strategy", "TODO: save the current strategy.")

    def _close_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "Close Strategy", "TODO: close the current strategy.")

    # --- Symbol management ---
    def _load_symbol_cache(self) -> Dict[str, str]:
        """Load A-share symbols (plus ETF) from cache; fetch via akshare if missing."""
        cache_path = Path(__file__).resolve().parents[3] / "data" / "symbols_a.csv"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.exists():
            try:
                df = pd.read_csv(cache_path, dtype=str)
                if {"code", "name"}.issubset(df.columns):
                    return dict(zip(df["code"], df["name"]))
            except Exception:
                pass  # fallback to fetch

        try:
            QtWidgets.QMessageBox.information(
                self,
                "Downloading",
                "Downloading A-share and ETF symbols to local cache...",
            )
            a_df = ak.stock_zh_a_spot_em()[["代码", "名称"]]
            etf_df = ak.fund_etf_spot_em()[["代码", "名称"]]
            df = pd.concat([a_df, etf_df], ignore_index=True)
            df = df.drop_duplicates(subset=["代码"]).rename(columns={"代码": "code", "名称": "name"})
            df = df.sort_values("code")
            df.to_csv(cache_path, index=False, encoding="utf-8")
            return dict(zip(df["code"], df["name"]))
        except Exception:
            QtWidgets.QMessageBox.warning(
                self,
                "Symbol Load Failed",
                "Failed to load symbols from akshare. Please check network and retry.",
            )
            return {}

    def _on_add_symbol(self) -> None:
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Symbol")
        dialog.resize(220, 140)
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        input_box = QtWidgets.QLineEdit()
        input_box.setPlaceholderText("Search by code or name...")
        completer = QtWidgets.QCompleter(self.completer_model, dialog)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        input_box.setCompleter(completer)

        def handle_completion(text: str) -> None:
            # Ensure only code is placed into the line edit when a suggestion is chosen.
            code = text.split()[0].strip().upper()
            input_box.setText(code)

        completer.activated.connect(handle_completion)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        def accept() -> None:
            code = self._resolve_input_to_code(input_box.text())
            if code not in self.symbol_map:
                QtWidgets.QMessageBox.warning(dialog, "Invalid", "Please enter a valid A-share symbol code.")
                return
            if self._symbol_exists(code):
                QtWidgets.QMessageBox.information(dialog, "Duplicate", "Symbol already added.")
                dialog.accept()
                return
            self._add_symbol_to_list(code)
            dialog.accept()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(input_box)
        layout.addWidget(buttons)

        dialog.exec()

    def _on_delete_symbol(self) -> None:
        items = self.symbol_list_widget.selectedItems()
        if not items:
            QtWidgets.QMessageBox.information(self, "Delete Symbol", "No symbol selected.")
            return
        for item in items:
            row = self.symbol_list_widget.row(item)
            self.symbol_list_widget.takeItem(row)

    def _symbol_exists(self, code: str) -> bool:
        return any(
            self.symbol_list_widget.item(i).text().startswith(code)
            for i in range(self.symbol_list_widget.count())
        )

    def _add_symbol_to_list(self, code: str) -> None:
        name = self.symbol_map.get(code, "")
        display = f"{code}  {name}" if name else code
        self.symbol_list_widget.addItem(display)

    def _resolve_input_to_code(self, text: str) -> str | None:
        t = text.strip()
        if not t:
            return None
        # Take first token as candidate code (handles "code name" from completer)
        code_token = t.split()[0].strip().upper()
        if code_token in self.symbol_map:
            return code_token
        # Exact name match
        if t in self.name_to_code:
            return self.name_to_code[t]
        # Fuzzy startswith search on code or name
        matches = [
            c
            for c, n in self.symbol_map.items()
            if c.startswith(code_token) or n.startswith(t)
        ]
        if len(matches) == 1:
            return matches[0]
        return None
