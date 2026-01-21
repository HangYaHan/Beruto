from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from PyQt6 import QtCore, QtGui, QtWidgets

try:
    from src.backtest.datatype import AccountState, Order, Position
except Exception:
    @dataclass
    class Position:  # fallback stub
        symbol: str
        volume: int
        avg_price: float
        last_price: float

        def market_value(self) -> float:
            return float(self.volume) * float(self.last_price)

        def unrealized_pnl(self) -> float:
            return (float(self.last_price) - float(self.avg_price)) * float(self.volume)

    @dataclass
    class AccountState:  # fallback stub
        date: datetime
        cash: float
        positions: Dict[str, Position]
        total_assets: float

    @dataclass
    class Order:  # fallback stub
        symbol: str
        volume: int
        price: Optional[float]
        status: str | None = None


class OrderPanel(QtWidgets.QWidget):
    """Displays orders for a specific day as a clean table with color-coded direction."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("Orders"))
        header.addStretch(1)
        layout.addLayout(header)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels(["Symbol", "Direction", "Volume", "Avg Price", "Status"])
        layout.addWidget(self.table, stretch=1)

    def load_orders(self, orders: List[Order]) -> None:
        self.table.setRowCount(0)
        for row, order in enumerate(orders or []):
            self.table.insertRow(row)
            symbol_item = QtWidgets.QTableWidgetItem(str(getattr(order, "symbol", "")))
            direction = "Buy" if getattr(order, "volume", 0) >= 0 else "Sell"
            dir_item = QtWidgets.QTableWidgetItem(direction)
            dir_color = QtGui.QColor("red") if direction == "Buy" else QtGui.QColor("green")
            dir_item.setForeground(QtGui.QBrush(dir_color))

            volume_item = QtWidgets.QTableWidgetItem(f"{getattr(order, 'volume', 0):,}")
            price_val = getattr(order, "price", None)
            price_item = QtWidgets.QTableWidgetItem("" if price_val is None else f"{float(price_val):,.4f}")
            status_text = getattr(order, "status", None)
            status_item = QtWidgets.QTableWidgetItem(status_text or "Pending")

            for col, item in enumerate((symbol_item, dir_item, volume_item, price_item, status_item)):
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()


class LiveStatus(QtWidgets.QWidget):
    """Shows the latest AccountState snapshot with metrics and positions."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._last_equity: Optional[float] = None
        self._last_date: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.lbl_date = QtWidgets.QLabel("--")
        self.lbl_date.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.lbl_date)

        metrics = QtWidgets.QGridLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(6)

        self.val_cash = QtWidgets.QLabel("--")
        self.val_assets = QtWidgets.QLabel("--")
        self.val_daily_ret = QtWidgets.QLabel("--")

        metrics.addWidget(QtWidgets.QLabel("Cash"), 0, 0)
        metrics.addWidget(self.val_cash, 0, 1)
        metrics.addWidget(QtWidgets.QLabel("Total Assets"), 1, 0)
        metrics.addWidget(self.val_assets, 1, 1)
        metrics.addWidget(QtWidgets.QLabel("Daily Return"), 2, 0)
        metrics.addWidget(self.val_daily_ret, 2, 1)

        layout.addLayout(metrics)

        positions_header = QtWidgets.QHBoxLayout()
        positions_header.addWidget(QtWidgets.QLabel("Positions"))
        positions_header.addStretch(1)
        layout.addLayout(positions_header)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels(["Symbol", "Volume", "Market Value", "Unrealized PnL"])
        layout.addWidget(self.table, stretch=1)

    def update_state(self, state: AccountState) -> None:
        date_str = state.date.strftime("%Y-%m-%d") if isinstance(state.date, datetime) else str(state.date)
        self.lbl_date.setText(date_str)

        cash = float(getattr(state, "cash", 0.0))
        total_assets = float(getattr(state, "total_assets", 0.0))
        self.val_cash.setText(f"{cash:,.2f}")
        self.val_assets.setText(f"{total_assets:,.2f}")

        daily_ret_text = "--"
        if self._last_equity is not None and (self._last_date is None or self._last_date == date_str):
            diff = total_assets - self._last_equity
            daily_ret = (diff / self._last_equity) * 100 if self._last_equity else 0.0
            daily_ret_text = f"{daily_ret:+.2f}%"
        elif self._last_date is not None and self._last_date != date_str:
            # reset daily return when date changes and no reference for the new day yet
            daily_ret_text = "--"
        self.val_daily_ret.setText(daily_ret_text)

        self._last_equity = total_assets
        self._last_date = date_str

        self._fill_positions(getattr(state, "positions", {}) or {})

    def _fill_positions(self, positions: Dict[str, Position]) -> None:
        self.table.setRowCount(0)
        for row, pos in enumerate(positions.values()):
            self.table.insertRow(row)
            symbol_item = QtWidgets.QTableWidgetItem(str(getattr(pos, "symbol", "")))
            vol_item = QtWidgets.QTableWidgetItem(f"{getattr(pos, 'volume', 0):,}")
            mv_val = pos.market_value() if hasattr(pos, "market_value") else float(getattr(pos, "last_price", 0.0)) * float(getattr(pos, "volume", 0))
            mv_item = QtWidgets.QTableWidgetItem(f"{mv_val:,.2f}")
            pnl_val = pos.unrealized_pnl() if hasattr(pos, "unrealized_pnl") else (float(getattr(pos, "last_price", 0.0)) - float(getattr(pos, "avg_price", 0.0))) * float(getattr(pos, "volume", 0))
            pnl_item = QtWidgets.QTableWidgetItem(f"{pnl_val:,.2f}")
            pnl_item.setForeground(QtGui.QBrush(QtGui.QColor("red" if pnl_val >= 0 else "green")))

            for col, item in enumerate((symbol_item, vol_item, mv_item, pnl_item)):
                align = QtCore.Qt.AlignmentFlag.AlignRight if col > 0 else QtCore.Qt.AlignmentFlag.AlignLeft
                item.setTextAlignment(align | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()


__all__ = ["OrderPanel", "LiveStatus"]
