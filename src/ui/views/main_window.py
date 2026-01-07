from __future__ import annotations

from pathlib import Path
from typing import Dict
from datetime import datetime

import akshare as ak
import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets

from src.system.CLI import execute_command
from src.ui.views.console_panel import ConsolePanel
from src.ui.views.kline_panel import KLineChartPanel, KlineDownloadWorker
from src.ui.views.plan_wizard import PlanWizardDialog
from src.ui.views.symbol_panel import SymbolsPanel
from src.ui.views.ui_utils import make_card
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
        self.kline_cache_dir = Path(__file__).resolve().parents[3] / "data" / "kline"
        self.kline_cache_dir.mkdir(parents=True, exist_ok=True)
        self.symbol_store_path = Path(__file__).resolve().parents[3] / "data" / "saved_symbols.txt"
        self.symbol_store_path.parent.mkdir(parents=True, exist_ok=True)
        self.saved_symbol_codes: set[str] = self._load_saved_symbol_codes()
        self._download_threads: list[QtCore.QThread] = []
        self._download_workers: list[QtCore.QObject] = []
        self.symbol_map: Dict[str, str] = self._load_symbol_cache()
        self.name_to_code: Dict[str, str] = {name: code for code, name in self.symbol_map.items()}
        self.suggestion_list = [f"{code} {name}" for code, name in self.symbol_map.items()]
        self._build_menu()
        self._build_layout()
        self._populate_saved_symbols()
        self._sync_console_action_label(False)

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

        file_menu = bar.addMenu("File")
        new_action = QtGui.QAction("New Plan", self)
        new_action.triggered.connect(self._new_strategy)
        open_action = QtGui.QAction("Open Plan", self)
        open_action.triggered.connect(self._open_strategy)
        save_action = QtGui.QAction("Save Plan", self)
        save_action.triggered.connect(self._save_strategy)
        close_action = QtGui.QAction("Close Plan", self)
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

        tabs.addTab(self._build_universe_tab(), "Universe")
        tabs.addTab(self._build_symbols_tab(), "Symbols")
        tabs.addTab(self._build_factors_tab(), "Factors")
        tabs.addTab(self._build_plan_tab(), "Plan / Arbiter")

        layout.addWidget(tabs)
        return wrapper

    def _build_universe_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(make_card("Universe Rules", "Dynamic pool filters: ST/PT, IPO age, suspension, delisting (placeholder)"))
        layout.addWidget(make_card("Constituents & Calendar", "Index constituents and trading calendar (placeholder)"))
        return widget

    def _build_symbols_tab(self) -> QtWidgets.QWidget:
        self.symbols_panel = SymbolsPanel(
            symbol_map=self.symbol_map,
            name_to_code=self.name_to_code,
            suggestion_list=self.suggestion_list,
            on_symbol_added=self._handle_symbol_added,
            on_symbols_deleted=self._handle_symbols_deleted,
            on_symbol_view=self._view_kline_for_code,
            register_tooltip=self._register_tooltip_target,
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

        vbox.addWidget(make_card("Plan", "Plan name, universe, benchmark (placeholder)"))
        vbox.addWidget(make_card("Arbiter", "Weights, thresholds, debounce parameters (placeholder)"))
        vbox.addWidget(make_card("Scheduler", "Rebalance frequency and triggers (placeholder)"))
        vbox.addWidget(make_card("Save / Apply", "Save draft / apply to backtest buttons (placeholder)"))
        return widget

    def _build_middle_tabs(self) -> QtWidgets.QWidget:
        tabs = QtWidgets.QTabWidget()
        self.kline_panel = KLineChartPanel(on_symbol_requested=self._view_kline_for_code, parent=self)
        tabs.addTab(self.kline_panel, "Chart")
        tabs.addTab(make_card("Signals", "Oracle signals aligned on timeline (placeholder)"), "Signals")
        tabs.addTab(make_card("Portfolio", "Target vs current holdings, rebalance diff (placeholder)"), "Portfolio")
        tabs.addTab(make_card("Orders", "Executor order preview and constraint checks (placeholder)"), "Orders")
        return tabs

    def _build_info_wall(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(8)

        vbox.addWidget(make_card("Live Status", "Cash / Equity / Exposure / Turnover / T+1 sellable (placeholder)"))
        vbox.addWidget(make_card("Risk Monitor", "Limit-up/down blocks, slippage/fee estimate, max DD, concentration (placeholder)"))
        vbox.addWidget(make_card("Task Queue", "Plan runs, data updates, download progress (placeholder)"))
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
        dlg.exec()

    def _open_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "Open Plan", "TODO: open an existing strategy plan.")

    def _save_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "Save Plan", "TODO: save the current strategy plan.")

    def _close_strategy(self) -> None:
        QtWidgets.QMessageBox.information(self, "Close Plan", "TODO: close the current strategy plan.")

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

    def _load_saved_symbol_codes(self) -> set[str]:
        try:
            return {
                line.strip().upper()
                for line in self.symbol_store_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            }
        except FileNotFoundError:
            return set()
        except Exception:
            return set()

    def _persist_saved_symbols(self) -> None:
        try:
            self.symbol_store_path.write_text(
                "\n".join(sorted(self.saved_symbol_codes)),
                encoding="utf-8",
            )
        except Exception as exc:
            self._log(f"Failed to persist symbols to {self.symbol_store_path}: {exc}")

    def _populate_saved_symbols(self) -> None:
        if not self.saved_symbol_codes or not hasattr(self, "symbols_panel"):
            return
        for code in sorted(self.saved_symbol_codes):
            if code not in self.symbol_map:
                self._log(f"Symbol {code} is saved locally but not in the current universe cache.")
            self.symbols_panel.add_symbol_display(code)

    def _add_symbol_to_saved(self, code: str) -> None:
        if code in self.saved_symbol_codes:
            return
        self.saved_symbol_codes.add(code)
        self._persist_saved_symbols()

    def _remove_symbols_from_saved(self, codes: list[str]) -> None:
        changed = False
        for code in codes:
            if code in self.saved_symbol_codes:
                self.saved_symbol_codes.remove(code)
                changed = True
            cache_path = self.kline_cache_dir / f"{code}.csv"
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    self._log(f"Deleted local data for {code} at {cache_path}")
                except Exception as exc:
                    self._log(f"Failed to delete {cache_path}: {exc}")
        if changed:
            self._persist_saved_symbols()
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
