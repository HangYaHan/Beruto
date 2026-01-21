from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets

from src.system.CLI import execute_command
from src.ui.controllers.main_controller import MainController
from src.ui.services.plan_storage import PlanStorage
from src.ui.services.symbol_service import SymbolDataService
from src.ui.views.calendar_view import FinancialCalendarWidget
from src.ui.views.console_panel import ConsolePanel
from src.ui.views.kline_panel import KLineChartPanel, KlineDownloadWorker
from src.ui.views.plan_wizard import PlanWizardDialog
from src.ui.views.symbol_panel import SymbolsPanel
from src.ui.views.visualizers import LiveStatus, OrderPanel
from src.ui.views.ui_utils import make_card
from src.system.settings import SettingsManager

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_task: str | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.default_task = default_task
        self.setWindowTitle("Beruto")
        icon_path = Path(__file__).resolve().parents[2] / "ui" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        self.resize(1920, 1080)
        self.move(0, 0)
        self._tooltip_delay_ms = 350  # shorten tooltip hover delay (~half default)
        self._tooltip_targets: Dict[QtWidgets.QWidget, str] = {}
        self.console_toggle_action: QtGui.QAction | None = None
        # Set early to avoid AttributeError when eventFilter is triggered before console creation.
        self.input: QtWidgets.QLineEdit | None = None
        self.project_root = Path(__file__).resolve().parents[3]
        self.kline_cache_dir = self.project_root / "data" / "kline"
        self.kline_cache_dir.mkdir(parents=True, exist_ok=True)

        self.settings = SettingsManager(project_root=self.project_root)
        self.symbol_service = SymbolDataService(self.project_root, self.settings, logger=self._log)
        self.plan_storage = PlanStorage()
        self.controller = MainController(window=self, project_root=self.project_root)
        self.history: list[Any] = []
        self.factors_data: Dict[str, Dict[str, Any]] = {}
        self._download_threads: list[QtCore.QThread] = []
        self._download_workers: list[QtCore.QObject] = []

        symbol_map = self.symbol_service.load_symbol_map()
        self._apply_symbol_sources(symbol_map)
        self.saved_symbol_codes: set[str] = set(self.symbol_service.get_saved_symbols())
        self.last_refresh_date = self.symbol_service.get_last_refresh_date()
        self.current_plan: Dict[str, Any] | None = None
        self.current_plan_path: Path | None = None
        self._build_menu()
        self._build_layout()
        self._populate_saved_symbols()
        self._sync_console_action_label(False)
        self._sync_plan_actions()
        if hasattr(self, "calendar_widget"):
            self.calendar_widget.date_selected.connect(self.on_replay_step)
        self._load_factors_from_settings()

    def _build_layout(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        outer = QtWidgets.QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(8)

        self.left_panel = self._build_left_panel()
        self.middle_panel = self._build_middle_tabs()
        self.right_panel = self._build_info_wall()

        top_row.addWidget(self.left_panel, stretch=1)
        top_row.addWidget(self.middle_panel, stretch=3)
        top_row.addWidget(self.right_panel, stretch=1)

        self.console = self._build_console()
        self.console.setVisible(False)

        outer.addLayout(top_row, stretch=5)
        outer.addWidget(self.console, stretch=2)

    def _build_menu(self) -> None:
        bar = self.menuBar()
        bar.setStyleSheet(
            "QMenuBar { padding: 0px; margin: 0px; spacing: 0px; border: 0px; border-radius: 0px; background: transparent; }"
            "QMenuBar::item { padding: 4px 8px; margin: 0px; border: 0px; border-radius: 0px; }"
            "QMenu::icon { padding: 0px; margin: 0px; width: 0px; }"
            "QMenu::item { padding: 6px 18px; margin: 2px 6px; min-width: 114px; }"
            "QMenu::item:selected { background: palette(Highlight); color: palette(HighlightedText); }"
        )

        # File menu: only Exit
        file_menu = bar.addMenu("File")
        exit_action = QtGui.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Run backtest for the current plan
        self.action_run_backtest = QtGui.QAction("Run Backtest", self)
        self.action_run_backtest.triggered.connect(self.controller.on_action_run_backtest_triggered)
        file_menu.addAction(self.action_run_backtest)

        # Plan menu
        plan_menu = bar.addMenu("Plan")
        self.action_new_plan = QtGui.QAction("New Plan", self)
        self.action_new_plan.triggered.connect(self._new_strategy)
        self.action_open_plan = QtGui.QAction("Open Plan", self)
        self.action_open_plan.triggered.connect(self._open_strategy)
        self.action_edit_plan = QtGui.QAction("Edit Plan", self)
        self.action_edit_plan.triggered.connect(self._edit_strategy)
        self.action_save_plan = QtGui.QAction("Save Plan", self)
        self.action_save_plan.triggered.connect(self._save_strategy)
        self.action_close_plan = QtGui.QAction("Close Plan", self)
        self.action_close_plan.triggered.connect(self._close_strategy)

        plan_menu.addAction(self.action_new_plan)
        plan_menu.addAction(self.action_open_plan)
        plan_menu.addSeparator()
        plan_menu.addAction(self.action_edit_plan)
        plan_menu.addAction(self.action_save_plan)
        plan_menu.addAction(self.action_close_plan)

        help_menu = bar.addMenu("Help")
        self.console_toggle_action = QtGui.QAction("Hide Console", self)
        self.console_toggle_action.triggered.connect(self._toggle_console)
        help_menu.addAction(self.console_toggle_action)
        help_menu.addSeparator()
        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _build_left_panel(self) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QFrame()
        layout = QtWidgets.QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        tabs = QtWidgets.QTabWidget()

        self.factor_list_widget = QtWidgets.QListWidget()
        self.factor_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.factor_list_widget.itemDoubleClicked.connect(self._handle_factor_double_clicked)

        tabs.addTab(self._build_universe_tab(), "Universe")
        tabs.addTab(self._build_symbols_tab(), "Symbols")
        tabs.addTab(self._build_factors_tab(), "Factors")
        tabs.addTab(self._build_plan_tab(), "Plan / Scoring")

        layout.addWidget(tabs)
        return wrapper

    def _build_universe_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        rules = make_card("Universe Rules", "Dynamic pool filters: ST/PT, IPO age, suspension, delisting (placeholder)")
        self.calendar_widget = FinancialCalendarWidget(parent=widget)
        self.calendar_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addWidget(rules, stretch=1)
        layout.addWidget(self.calendar_widget, stretch=2)
        return widget

    def _build_symbols_tab(self) -> QtWidgets.QWidget:
        self.symbols_panel = SymbolsPanel(
            symbol_map=self.symbol_map,
            name_to_code=self.name_to_code,
            suggestion_list=self.suggestion_list,
            on_symbol_added=self._handle_symbol_added,
            on_symbols_deleted=self._handle_symbols_deleted,
            on_refresh_requested=self._refresh_all_symbol_data,
            on_symbol_view=self._view_kline_for_code,
            register_tooltip=self._register_tooltip_target,
            last_refresh_date=self.last_refresh_date,
            parent=self,
        )
        return self.symbols_panel

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

        vbox.addWidget(make_card("Factor Pipeline", "Enable/disable, grouping, params, signal coverage (placeholder)"))

        return widget

    def _build_plan_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(8)

        # Summary group (updates when a plan is opened/closed)
        self.plan_summary_group = QtWidgets.QGroupBox("Plan Summary")
        sg_layout = QtWidgets.QVBoxLayout(self.plan_summary_group)
        self.plan_summary_label = QtWidgets.QLabel("No plan opened.")
        self.plan_summary_label.setWordWrap(True)
        sg_layout.addWidget(self.plan_summary_label)
        vbox.addWidget(self.plan_summary_group)

        vbox.addWidget(make_card("Plan", "Plan name, universe, benchmark (placeholder)"))
        vbox.addWidget(make_card("Scoring", "Weights, thresholds, debounce parameters (placeholder)"))
        vbox.addWidget(make_card("Scheduler", "Rebalance frequency and triggers (placeholder)"))
        return widget

    def _build_middle_tabs(self) -> QtWidgets.QWidget:
        tabs = QtWidgets.QTabWidget()
        self.chart_stack = QtWidgets.QStackedWidget()
        self.kline_panel = KLineChartPanel(on_symbol_requested=self._view_kline_for_code, parent=self)
        self.chart_stack.addWidget(self.kline_panel)
        self.factor_help_panel = self._build_factor_help_panel()
        self.chart_stack.addWidget(self.factor_help_panel)
        tabs.addTab(self.chart_stack, "Chart")
        tabs.addTab(make_card("Signals", "Factor signals aligned on timeline (placeholder)"), "Signals")
        tabs.addTab(make_card("Portfolio", "Target vs current holdings, rebalance diff (placeholder)"), "Portfolio")
        self.order_panel = OrderPanel(parent=self)
        tabs.addTab(self.order_panel, "Orders")
        return tabs

    def _build_factor_help_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.factor_help_title = QtWidgets.QLabel("Factor Help")
        self.factor_help_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.factor_help_body = QtWidgets.QTextEdit()
        self.factor_help_body.setReadOnly(True)
        self.factor_help_body.setPlaceholderText("Double-click a factor to view its help text.")
        layout.addWidget(self.factor_help_title)
        layout.addWidget(self.factor_help_body)
        return panel

    def _build_info_wall(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(8)
        self.live_status = LiveStatus(parent=frame)
        vbox.addWidget(self.live_status, stretch=2)

        self.global_info = QtWidgets.QLabel("--")
        self.global_info.setWordWrap(True)
        gbox = QtWidgets.QGroupBox("Global Metrics")
        gl = QtWidgets.QVBoxLayout(gbox)
        gl.addWidget(self.global_info)
        vbox.addWidget(gbox)

        risk_monitor = make_card("Risk Monitor", "Limit-up/down blocks, slippage/fee estimate, max DD, concentration (placeholder)")
        vbox.addWidget(risk_monitor, stretch=1)
        return frame

    def _build_console(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QTabWidget()
        console = ConsolePanel(on_command=self._handle_command, parent=self)
        self.log_view = console.log_view
        self.input = console.input
        tab.addTab(console, "Console")

        recent_log = QtWidgets.QPlainTextEdit()
        recent_log.setReadOnly(True)
        recent_log.setPlainText("Recent task logs placeholder: filter (error/warn/info), copy all")
        tab.addTab(recent_log, "Recent Logs")
        return tab

    def _handle_command(self, cmd: str) -> None:
        try:
            res = execute_command(cmd, write=self._append_log)
            if res and res.get("type") in {"image", "images"}:
                paths = res.get("paths") or [res.get("path")]
                if paths:
                    self._append_log("Output files:")
                    for path in paths:
                        self._append_log(f"  {path}")
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
        return super().eventFilter(obj, event)

    def _register_tooltip_target(self, widget: QtWidgets.QWidget, text: str) -> None:
        self._tooltip_targets[widget] = text
        widget.setToolTip(text)
        widget.installEventFilter(self)

    def _show_tooltip_if_hovered(self, widget: QtCore.QObject) -> None:
        if isinstance(widget, QtWidgets.QWidget) and widget.underMouse():
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), widget.toolTip(), widget)

    def _toggle_console(self) -> None:
        if not hasattr(self, "console") or self.console is None:
            return
        new_visible = not self.console.isVisible()
        self.console.setVisible(new_visible)
        self._sync_console_action_label(new_visible)
        if new_visible and self.input:
            self.input.setFocus()

    def _sync_console_action_label(self, visible: bool) -> None:
        if self.console_toggle_action is None:
            return
        self.console_toggle_action.setText("Hide Console" if visible else "Show Console")

    def _append_log(self, text: str) -> None:
        self.log_view.appendPlainText(text)

    def _log(self, text: str) -> None:
        self._append_log(text)
        try:
            print(text)
        except Exception:
            pass

    def _show_about_dialog(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "\nThis is the GUI version of Beruto.\n",
        )

    # --- Plan menu handlers ---
    def _new_strategy(self) -> None:
        dlg = PlanWizardDialog(self)
        result = dlg.exec()
        # After creating a new plan, auto-open it once if saved
        try:
            created_path = getattr(dlg, "created_plan_path", None)
        except Exception:
            created_path = None
        if result == QtWidgets.QDialog.DialogCode.Accepted and created_path:
            self._load_plan_from_path(Path(created_path))

    def _open_strategy(self) -> None:
        path_str, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Plan JSON",
            str(self.project_root / "plan"),
            "JSON Files (*.json)"
        )
        if not path_str:
            return
        self._load_plan_from_path(Path(path_str))

    def _save_strategy(self) -> None:
        if not self.current_plan:
            QtWidgets.QMessageBox.information(self, "Save Plan", "No plan to save.")
            return
        if not self.current_plan_path:
            path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Plan JSON",
                str(self.project_root / "plan" / "plan.json"),
                "JSON Files (*.json)"
            )
            if not path_str:
                return
            self.current_plan_path = Path(path_str)
        try:
            self.plan_storage.save(self.current_plan, self.current_plan_path)
            QtWidgets.QMessageBox.information(self, "Saved", f"Plan saved to: {self.current_plan_path}")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Save Failed", str(exc))

    def _close_strategy(self) -> None:
        # Clear current plan and update UI summary
        self.current_plan = None
        self.current_plan_path = None
        self._update_plan_summary(None)
        QtWidgets.QMessageBox.information(self, "Close Plan", "Plan closed.")
        self._sync_plan_actions()

    def _edit_strategy(self) -> None:
        # Open the current plan file in the default editor for quick edits
        if not self.current_plan_path:
            QtWidgets.QMessageBox.information(self, "Edit Plan", "No plan opened. Open or create a plan first.")
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.current_plan_path)))

    def _load_plan_from_path(self, path: Path) -> None:
        try:
            plan = self.plan_storage.load(path)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Open Failed", f"Failed to open plan: {exc}")
            return
        self.current_plan = plan
        self.current_plan_path = path
        self._update_plan_summary(plan)
        self._log(f"Opened plan from {path}")
        self._sync_plan_actions()

    def _update_plan_summary(self, plan: Dict[str, Any] | None) -> None:
        if not hasattr(self, "plan_summary_label") or self.plan_summary_label is None:
            return
        if not plan:
            self.plan_summary_label.setText("No plan opened.")
            return
        summary = self.plan_storage.summary_lines(plan, self.current_plan_path)
        self.plan_summary_label.setText(summary)

    def _sync_plan_actions(self) -> None:
        has_plan = self.current_plan is not None
        # When no plan is open: enable New/Open; disable Edit/Save/Close
        # When a plan is open: disable New/Open; enable Edit/Save/Close
        for action, enabled in (
            (getattr(self, "action_new_plan", None), not has_plan),
            (getattr(self, "action_open_plan", None), not has_plan),
            (getattr(self, "action_edit_plan", None), has_plan),
            (getattr(self, "action_save_plan", None), has_plan),
            (getattr(self, "action_close_plan", None), has_plan),
        ):
            if action is not None:
                action.setEnabled(enabled)

    # --- Backtest replay ---
    def update_global_info(self, metrics: Dict[str, Any]) -> None:
        if not hasattr(self, "global_info") or self.global_info is None:
            return
        total_ret = metrics.get("total_return") if isinstance(metrics, dict) else None
        mdd = metrics.get("max_drawdown") if isinstance(metrics, dict) else None
        parts = []
        if total_ret is not None:
            parts.append(f"Total Return: {total_ret:+.2%}")
        if mdd is not None:
            parts.append(f"Max DD: {mdd:.2%}")
        self.global_info.setText(" | ".join(parts) if parts else "--")

    @QtCore.pyqtSlot(int)
    def on_replay_step(self, index: int) -> None:
        history: List[Any] = getattr(self.controller, "history", None) or getattr(self, "history", [])
        if not history:
            return
        if index < 0 or index >= len(history):
            return
        state = history[index]
        if hasattr(self, "live_status"):
            try:
                self.live_status.update_state(state)
            except Exception as exc:
                self._log(f"LiveStatus update failed: {exc}")
        orders = getattr(state, "orders", None) or []
        if hasattr(self, "order_panel"):
            try:
                self.order_panel.load_orders(orders)
            except Exception as exc:
                self._log(f"OrderPanel update failed: {exc}")

    # --- Symbol management ---
    def _apply_symbol_sources(self, symbol_map: Dict[str, str]) -> None:
        self.symbol_map = symbol_map or {}
        self.name_to_code = self.symbol_service.get_name_to_code()
        self.suggestion_list = self.symbol_service.get_suggestions()

    def _populate_saved_symbols(self) -> None:
        if not self.saved_symbol_codes or not hasattr(self, "symbols_panel"):
            return
        for code in sorted(self.saved_symbol_codes):
            if code not in self.symbol_map:
                self._log(f"Symbol {code} is saved locally but not in the current universe cache.")
            self.symbols_panel.add_symbol_display(code)

    def _add_symbol_to_saved(self, code: str) -> None:
        normalized = code.strip().upper()
        if not normalized or normalized in self.saved_symbol_codes:
            return
        self.saved_symbol_codes.add(normalized)
        self.symbol_service.add_saved_symbol(normalized)

    def _remove_symbols_from_saved(self, codes: list[str]) -> None:
        normalized = {c.strip().upper() for c in codes if c.strip()}
        if not normalized:
            return
        self.saved_symbol_codes -= normalized
        self.symbol_service.remove_saved_symbols(list(normalized))
        for code in normalized:
            cache_path = self.kline_cache_dir / f"{code}.csv"
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    self._log(f"Deleted local data for {code} at {cache_path}")
                except Exception as exc:
                    self._log(f"Failed to delete {cache_path}: {exc}")

    def _refresh_all_symbol_data(self) -> None:
        if not self.saved_symbol_codes:
            QtWidgets.QMessageBox.information(self, "Refresh", "No saved symbols to refresh.")
            return
        codes = sorted(self.saved_symbol_codes)
        for code in codes:
            cache_path = self.kline_cache_dir / f"{code}.csv"
            self._download_kline_with_progress(code, cache_path)
        today = datetime.now().strftime("%Y-%m-%d")
        self.symbol_service.set_last_refresh_date(today)
        self.last_refresh_date = today
        if hasattr(self, "symbols_panel"):
            self.symbols_panel.set_last_refresh_date(today)

    def _refresh_symbol_universe(self) -> None:
        new_map = self.symbol_service.fetch_and_cache_symbols()
        if not new_map:
            QtWidgets.QMessageBox.warning(self, "Symbol Load Failed", "Failed to load symbols. Please retry.")
            return
        self._apply_symbol_sources(new_map)
        if hasattr(self, "symbols_panel"):
            self.symbols_panel.update_symbol_sources(self.symbol_map, self.name_to_code, self.suggestion_list)
            self.symbols_panel.set_last_refresh_date(self.symbol_service.get_last_refresh_date())
        self.last_refresh_date = self.symbol_service.get_last_refresh_date()

    # --- Factors management ---
    def _load_factors_from_settings(self) -> None:
        factors = getattr(self.settings, "settings", None)
        factors_map = factors.factors if factors else {}
        self.factors_data = factors_map or {}
        self.factor_list_widget.clear()
        for name in sorted(self.factors_data.keys()):
            item = QtWidgets.QListWidgetItem(name)
            self.factor_list_widget.addItem(item)

    def _handle_factor_double_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        name = item.text().strip()
        help_text = self._load_factor_help_text(name)
        self._show_factor_help(name, help_text)

    def _load_factor_help_text(self, name: str) -> str:
        # Prefer dedicated factor json if exists, else settings help
        factor_path = self.project_root / "data" / "factors" / f"{name}.json"
        if factor_path.exists():
            try:
                with factor_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data.get("help"):
                        return str(data.get("help"))
            except Exception:
                pass
        info = self.factors_data.get(name) or {}
        return str(info.get("help", "No help text available for this factor."))

    def _show_factor_help(self, name: str, text: str) -> None:
        if hasattr(self, "factor_help_title"):
            self.factor_help_title.setText(f"Factor: {name}")
        if hasattr(self, "factor_help_body"):
            self.factor_help_body.setPlainText(text or "No help text available.")
        if hasattr(self, "chart_stack"):
            self.chart_stack.setCurrentWidget(self.factor_help_panel)
        if hasattr(self, "middle_panel"):
            idx = self.middle_panel.indexOf(self.chart_stack)
            if idx >= 0:
                self.middle_panel.setCurrentIndex(idx)
                self.middle_panel.setTabText(idx, "Factor Help")

    def _show_chart_view(self) -> None:
        if hasattr(self, "chart_stack"):
            self.chart_stack.setCurrentWidget(self.kline_panel)
        if hasattr(self, "middle_panel"):
            idx = self.middle_panel.indexOf(self.chart_stack)
            if idx >= 0:
                self.middle_panel.setCurrentIndex(idx)
                self.middle_panel.setTabText(idx, "Chart")

    def _handle_symbol_added(self, code: str) -> None:
        self._add_symbol_to_saved(code)
        self._download_kline_if_missing(code)

    def _handle_symbols_deleted(self, codes: list[str]) -> None:
        if not codes:
            return
        self._remove_symbols_from_saved(codes)

    def _view_kline_for_code(self, code: str | None) -> None:
        if not code:
            QtWidgets.QMessageBox.warning(self, "Invalid", "Symbol code is empty.")
            return
        self._show_chart_view()
        normalized = code.strip().upper()
        if normalized not in self.symbol_map:
            QtWidgets.QMessageBox.warning(self, "Not Found", f"Symbol {normalized} is not in the list.")
            return
        cache_path = self.kline_cache_dir / f"{normalized}.csv"
        if cache_path.exists():
            try:
                df = self._load_kline_from_cache(cache_path)
                self._log(f"Loaded {normalized} K-line from cache {cache_path}")
                self.kline_panel.display_symbol(normalized, df)
                return
            except Exception as exc:  # fallback to fresh download
                self._log(f"Failed to read cached K-line for {normalized}: {exc}; downloading fresh data...")
        self._download_kline_with_progress(normalized, cache_path)

    def _download_kline_if_missing(self, code: str) -> None:
        cache_path = self.kline_cache_dir / f"{code}.csv"
        if cache_path.exists():
            self._log(f"Skip download: {code} cache already exists at {cache_path}")
            return
        self._download_kline_with_progress(code, cache_path)

    def _load_kline_from_cache(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path)
        if "date" not in df.columns:
            raise ValueError("Invalid cache file format: missing date column")
        df["date"] = pd.to_datetime(df["date"])
        required = {"open", "high", "low", "close"}
        if not required.issubset(df.columns):
            raise ValueError("Invalid cache file format: missing price columns")
        return df

    def _download_kline_with_progress(self, code: str, cache_path: Path) -> None:
        progress = QtWidgets.QProgressDialog("正在下载K线数据...", None, 0, 100, self)
        progress.setWindowTitle("Downloading")
        progress.setCancelButton(None)
        progress.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        worker = KlineDownloadWorker(
            code=code,
            start_date="20240101",
            end_date=datetime.now().strftime("%Y%m%d"),
            cache_path=cache_path,
        )
        thread = QtCore.QThread(self)
        worker.moveToThread(thread)

        worker.progress.connect(progress.setValue)
        worker.message.connect(progress.setLabelText)
        worker.message.connect(self._log)

        def handle_success(df: pd.DataFrame) -> None:
            progress.setValue(100)
            progress.close()
            self._log(f"{code} K-line downloaded to {cache_path}")
            self.kline_panel.display_symbol(code, df)

        def handle_error(msg: str) -> None:
            progress.close()
            QtWidgets.QMessageBox.warning(self, "Download Failed", msg)
            self._log(f"Failed to download {code}: {msg}")

        worker.finished.connect(handle_success)
        worker.error.connect(handle_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)

        def cleanup_thread() -> None:
            try:
                self._download_threads.remove(thread)
            except ValueError:
                pass
            try:
                self._download_workers.remove(worker)
            except ValueError:
                pass
            thread.deleteLater()

        thread.finished.connect(cleanup_thread)
        thread.started.connect(worker.run)

        self._download_threads.append(thread)
        self._download_workers.append(worker)
        self._log(f"Downloading {code} K-line via akshare from 2024-01-01 to {datetime.now().date()}...")
        thread.start()
