from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets

try:
    # Prefer real AccountState from backtest
    from src.backtest.datatype import AccountState
except Exception:
    @dataclass
    class AccountState:  # fallback typing stub
        date: datetime
        cash: float
        positions: Dict[str, Any]
        total_assets: float


class FinancialCalendarWidget(QtWidgets.QWidget):
    """
    A navigable financial calendar for backtest history.

    - Modes: Daily, Weekly, Yearly
    - View: QTableWidget with columns [Date, Daily PnL, Total Equity]
    - Navigation: step back/forward, jump to start/end
    - Signals: date_selected(index: int)
    """

    # Emitted with original history index (daily index or period-end index)
    date_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._history: List[AccountState] = []
        self._index_map: List[int] = []  # row -> original history index
        self._current_row: int = -1

        self._build_ui()
        self._wire_signals()

    # --- UI ---
    def _build_ui(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # Header: mode + nav
        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(["Daily", "Weekly", "Yearly"])
        header.addWidget(QtWidgets.QLabel("View:"))
        header.addWidget(self.mode)
        header.addStretch(1)

        self.btn_jump_start = QtWidgets.QPushButton("<<")
        self.btn_prev = QtWidgets.QPushButton("<")
        self.btn_next = QtWidgets.QPushButton(">")
        self.btn_jump_end = QtWidgets.QPushButton(">>")
        for b in (self.btn_jump_start, self.btn_prev, self.btn_next, self.btn_jump_end):
            b.setFixedWidth(40)
        header.addWidget(self.btn_jump_start)
        header.addWidget(self.btn_prev)
        header.addWidget(self.btn_next)
        header.addWidget(self.btn_jump_end)

        outer.addLayout(header)

        # Table
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.table.setHorizontalHeaderLabels(["Date", "Daily PnL", "Total Equity"])
        outer.addWidget(self.table, stretch=1)

    def _wire_signals(self) -> None:
        self.mode.currentTextChanged.connect(self._on_mode_changed)
        self.btn_prev.clicked.connect(self.prev_day)
        self.btn_next.clicked.connect(self.next_day)
        self.btn_jump_start.clicked.connect(self._jump_to_start)
        self.btn_jump_end.clicked.connect(self._jump_to_end)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_double_clicked)

    # --- Public slots ---
    @QtCore.pyqtSlot(list)
    def load_history(self, history: List[AccountState]) -> None:
        self._history = list(history or [])
        self._rebuild_view()

    @QtCore.pyqtSlot()
    def next_day(self) -> None:
        if self._current_row < 0:
            self._select_row(0)
            return
        self._select_row(min(self._current_row + 1, max(0, self.table.rowCount() - 1)))

    @QtCore.pyqtSlot()
    def prev_day(self) -> None:
        if self._current_row < 0:
            self._select_row(0)
            return
        self._select_row(max(self._current_row - 1, 0))

    # --- Internals ---
    def _on_mode_changed(self, _: str) -> None:
        self._rebuild_view()

    def _jump_to_start(self) -> None:
        if self.table.rowCount() > 0:
            self._select_row(0)

    def _jump_to_end(self) -> None:
        if self.table.rowCount() > 0:
            self._select_row(self.table.rowCount() - 1)

    def _on_selection_changed(self) -> None:
        row = self._current_selected_row()
        if row is None:
            return
        self._current_row = row
        if 0 <= row < len(self._index_map):
            self.date_selected.emit(self._index_map[row])

    def _on_double_clicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        row = item.row()
        self._current_row = row
        if 0 <= row < len(self._index_map):
            self.date_selected.emit(self._index_map[row])

    def _current_selected_row(self) -> Optional[int]:
        selected = self.table.selectionModel().selectedRows()
        if selected:
            return selected[0].row()
        return None

    def _select_row(self, row: int) -> None:
        if not (0 <= row < self.table.rowCount()):
            return
        self.table.selectRow(row)
        self.table.scrollToItem(self.table.item(row, 0), QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)
        self._current_row = row
        if 0 <= row < len(self._index_map):
            self.date_selected.emit(self._index_map[row])

    def _rebuild_view(self) -> None:
        mode = (self.mode.currentText() or "Daily").lower()
        rows, index_map = self._aggregate(self._history, mode)
        self._fill_table(rows)
        self._index_map = index_map
        self._current_row = -1
        if self.table.rowCount() > 0:
            self._select_row(0)

    def _fill_table(self, rows: List[Tuple[str, float, float]]) -> None:
        self.table.setRowCount(0)
        for r, (date_str, pnl, equity) in enumerate(rows):
            self.table.insertRow(r)
            # Date
            item_date = QtWidgets.QTableWidgetItem(date_str)
            item_date.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            # PnL with color-coded text (red for positive, green for negative per spec)
            item_pnl = QtWidgets.QTableWidgetItem(f"{pnl:,.2f}")
            item_pnl.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            if pnl > 0:
                item_pnl.setForeground(QtGui.QBrush(QtGui.QColor("red")))
            elif pnl < 0:
                item_pnl.setForeground(QtGui.QBrush(QtGui.QColor("green")))
            # Equity
            item_eq = QtWidgets.QTableWidgetItem(f"{equity:,.2f}")
            item_eq.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

            self.table.setItem(r, 0, item_date)
            self.table.setItem(r, 1, item_pnl)
            self.table.setItem(r, 2, item_eq)

        self.table.resizeColumnsToContents()

    # --- Aggregation helpers ---
    def _aggregate(self, history: List[AccountState], mode: str) -> Tuple[List[Tuple[str, float, float]], List[int]]:
        if not history:
            return [], []
        mode = mode.lower()
        if mode == "daily":
            return self._aggregate_daily(history)
        if mode == "weekly":
            return self._aggregate_weekly(history)
        if mode == "yearly":
            return self._aggregate_yearly(history)
        return self._aggregate_daily(history)

    def _aggregate_daily(self, history: List[AccountState]) -> Tuple[List[Tuple[str, float, float]], List[int]]:
        rows: List[Tuple[str, float, float]] = []
        index_map: List[int] = []
        prev_equity: Optional[float] = None
        for idx, st in enumerate(history):
            eq = float(st.total_assets)
            pnl = (eq - prev_equity) if (prev_equity is not None) else 0.0
            prev_equity = eq
            rows.append((st.date.strftime("%Y-%m-%d"), pnl, eq))
            index_map.append(idx)
        return rows, index_map

    def _aggregate_weekly(self, history: List[AccountState]) -> Tuple[List[Tuple[str, float, float]], List[int]]:
        rows: List[Tuple[str, float, float]] = []
        index_map: List[int] = []
        if not history:
            return rows, index_map
        # Group by ISO year-week; sum PnL; equity at period end
        start_equity: Optional[float] = None
        cur_year_week: Optional[Tuple[int, int]] = None
        acc_pnl: float = 0.0
        last_eq: float = 0.0
        last_idx: int = 0
        for i, st in enumerate(history):
            y, w, _ = st.date.isocalendar()
            key = (y, w)
            eq = float(st.total_assets)
            if cur_year_week is None:
                cur_year_week = key
                start_equity = eq
                acc_pnl = 0.0
            if key != cur_year_week:
                # finalize previous period
                rows.append((self._week_label(cur_year_week), acc_pnl, last_eq))
                index_map.append(last_idx)
                # start new period
                cur_year_week = key
                start_equity = eq
                acc_pnl = 0.0
            # daily pnl contribution
            if start_equity is not None:
                daily_pnl = eq - (float(history[i - 1].total_assets) if i > 0 and history[i - 1].date.isocalendar()[:2] == key else start_equity)
                acc_pnl += daily_pnl
            last_eq = eq
            last_idx = i
        # finalize last period
        if cur_year_week is not None:
            rows.append((self._week_label(cur_year_week), acc_pnl, last_eq))
            index_map.append(last_idx)
        return rows, index_map

    def _aggregate_yearly(self, history: List[AccountState]) -> Tuple[List[Tuple[str, float, float]], List[int]]:
        rows: List[Tuple[str, float, float]] = []
        index_map: List[int] = []
        if not history:
            return rows, index_map
        cur_year: Optional[int] = None
        start_equity: Optional[float] = None
        acc_pnl: float = 0.0
        last_eq: float = 0.0
        last_idx: int = 0
        for i, st in enumerate(history):
            y = st.date.year
            eq = float(st.total_assets)
            if cur_year is None:
                cur_year = y
                start_equity = eq
                acc_pnl = 0.0
            if y != cur_year:
                rows.append((str(cur_year), acc_pnl, last_eq))
                index_map.append(last_idx)
                cur_year = y
                start_equity = eq
                acc_pnl = 0.0
            # daily pnl contribution
            if start_equity is not None:
                daily_pnl = eq - (float(history[i - 1].total_assets) if i > 0 and history[i - 1].date.year == y else start_equity)
                acc_pnl += daily_pnl
            last_eq = eq
            last_idx = i
        if cur_year is not None:
            rows.append((str(cur_year), acc_pnl, last_eq))
            index_map.append(last_idx)
        return rows, index_map

    def _week_label(self, year_week: Tuple[int, int]) -> str:
        y, w = year_week
        return f"{y}-W{w:02d}"

    # Key navigation: emit selection on Up/Down arrows
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802 (Qt override)
        key = event.key()
        if key in (QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Left):
            self.prev_day()
            event.accept()
            return
        if key in (QtCore.Qt.Key.Key_Down, QtCore.Qt.Key.Key_Right):
            self.next_day()
            event.accept()
            return
        super().keyPressEvent(event)


__all__ = ["FinancialCalendarWidget"]
