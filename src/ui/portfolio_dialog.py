from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import PortfolioConfig, StrategySpec, SymbolSpec

@dataclass
class DialogDefaults:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    seed_symbol: str | None = None
    cached_symbols: list[str] | None = None


class PortfolioConfigDialog(QDialog):
    def __init__(self, defaults: DialogDefaults, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.defaults = defaults
        self.strategy_catalog = self._load_strategy_catalog()
        self.strategy_options = list(self.strategy_catalog.keys())
        self.setWindowTitle("组合回测配置")
        self.resize(900, 680)

        self._build_ui()
        self._init_defaults()

    def _load_strategy_catalog(self) -> dict[str, dict]:
        catalog_path = Path(__file__).resolve().parents[1] / "core" / "strategies" / "catalog.json"
        if not catalog_path.exists():
            raise ValueError(f"策略目录文件不存在: {catalog_path}")

        with catalog_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict) or not isinstance(data.get("strategies"), list):
            raise ValueError("策略目录格式错误: 缺少 strategies 列表")

        out: dict[str, dict] = {}
        for row in data["strategies"]:
            if not isinstance(row, dict):
                raise ValueError("策略目录格式错误: strategy 项必须是对象")
            sid = str(row.get("id", "")).strip()
            params = row.get("params", {})
            if not sid:
                raise ValueError("策略目录格式错误: strategy.id 不能为空")
            if not isinstance(params, dict):
                raise ValueError(f"策略目录格式错误: {sid}.params 必须是对象")
            out[sid] = row

        if not out:
            raise ValueError("策略目录为空")
        return out

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        top_form = QFormLayout()
        self.initial_cash_input = QLineEdit("")
        self.initial_cash_input.setPlaceholderText("例如: 1000000")

        self.fee_rate_input = QDoubleSpinBox()
        self.fee_rate_input.setRange(0.0, 0.05)
        self.fee_rate_input.setDecimals(4)
        self.fee_rate_input.setSingleStep(0.0005)
        self.fee_rate_input.setValue(0.0)

        self.start_date_text = QLineEdit(self.defaults.start_date.strftime("%Y-%m-%d"))
        self.end_date_text = QLineEdit(self.defaults.end_date.strftime("%Y-%m-%d"))

        top_form.addRow("初始资金:", self.initial_cash_input)
        top_form.addRow("费率(单边):", self.fee_rate_input)
        top_form.addRow("开始日期(YYYY-MM-DD):", self.start_date_text)
        top_form.addRow("结束日期(YYYY-MM-DD):", self.end_date_text)

        root.addLayout(top_form)

        tables = QGridLayout()

        self.symbol_table = QTableWidget(0, 2)
        self.symbol_table.setHorizontalHeaderLabels(["Symbol", "Weight(0-1)"])
        tables.addWidget(QLabel("标的列表"), 0, 0)
        tables.addWidget(self.symbol_table, 1, 0)

        symbol_btns = QHBoxLayout()
        self.add_symbol_btn = QPushButton("新增标的")
        self.remove_symbol_btn = QPushButton("删除标的")
        symbol_btns.addWidget(self.add_symbol_btn)
        symbol_btns.addWidget(self.remove_symbol_btn)
        tables.addLayout(symbol_btns, 2, 0)

        self.strategy_table = QTableWidget(0, 4)
        self.strategy_table.setHorizontalHeaderLabels(["Symbol", "Strategy", "x_pct", "y_pct"])
        tables.addWidget(QLabel("策略映射(可多行绑定同一Symbol)"), 0, 1)
        tables.addWidget(self.strategy_table, 1, 1)

        strat_btns = QHBoxLayout()
        self.add_strategy_btn = QPushButton("新增策略绑定")
        self.remove_strategy_btn = QPushButton("删除策略绑定")
        strat_btns.addWidget(self.add_strategy_btn)
        strat_btns.addWidget(self.remove_strategy_btn)
        tables.addLayout(strat_btns, 2, 1)

        root.addLayout(tables)

        help_label = QLabel("策略名可选: " + " / ".join(self.strategy_options))
        root.addWidget(help_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        root.addWidget(self.buttons)

        self.add_symbol_btn.clicked.connect(self.add_symbol_row)
        self.remove_symbol_btn.clicked.connect(self.remove_symbol_row)
        self.add_strategy_btn.clicked.connect(self.add_strategy_row)
        self.remove_strategy_btn.clicked.connect(self.remove_strategy_row)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _init_defaults(self) -> None:
        # Intentionally keep all defaults empty by user request.
        return

    def _symbol_options(self) -> list[str]:
        symbols: list[str] = []
        for row in range(self.symbol_table.rowCount()):
            item = self.symbol_table.item(row, 0)
            if item is None:
                continue
            s = item.text().strip()
            if s and s not in symbols:
                symbols.append(s)
        return symbols

    def _refresh_strategy_symbol_options(self) -> None:
        symbols = self._symbol_options()
        for row in range(self.strategy_table.rowCount()):
            combo = self.strategy_table.cellWidget(row, 0)
            if not isinstance(combo, QComboBox):
                continue
            selected = combo.currentText().strip()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(symbols)
            if selected and selected in symbols:
                combo.setCurrentText(selected)
            combo.blockSignals(False)

    def _strategy_param_defaults(self, strategy_id: str) -> tuple[float, float]:
        row = self.strategy_catalog.get(strategy_id, {})
        params = row.get("params", {}) if isinstance(row, dict) else {}
        x_default = float(params.get("x_pct", {}).get("default", 0.0)) if isinstance(params.get("x_pct"), dict) else 0.0
        y_default = float(params.get("y_pct", {}).get("default", 0.0)) if isinstance(params.get("y_pct"), dict) else 0.0
        return x_default, y_default

    def add_symbol_row(self, symbol: str = "", weight: float = 0.0) -> None:
        row = self.symbol_table.rowCount()
        self.symbol_table.insertRow(row)
        self.symbol_table.setItem(row, 0, QTableWidgetItem(symbol))
        self.symbol_table.setItem(row, 1, QTableWidgetItem(f"{weight:.4f}"))
        self._refresh_strategy_symbol_options()

    def remove_symbol_row(self) -> None:
        row = self.symbol_table.currentRow()
        if row >= 0:
            self.symbol_table.removeRow(row)
            self._refresh_strategy_symbol_options()

    def add_strategy_row(self, symbol: str = "", strategy: str = "do_nothing", x_pct: float = 0.0, y_pct: float = 0.0) -> None:
        row = self.strategy_table.rowCount()
        self.strategy_table.insertRow(row)

        symbol_combo = QComboBox()
        symbol_combo.addItems(self._symbol_options())
        if symbol and symbol in self._symbol_options():
            symbol_combo.setCurrentText(symbol)
        self.strategy_table.setCellWidget(row, 0, symbol_combo)

        strategy_combo = QComboBox()
        strategy_combo.addItems(self.strategy_options)
        if strategy and strategy in self.strategy_options:
            strategy_combo.setCurrentText(strategy)
        self.strategy_table.setCellWidget(row, 1, strategy_combo)

        x_input = QDoubleSpinBox()
        x_input.setRange(0.0, 1.0)
        x_input.setDecimals(4)
        y_input = QDoubleSpinBox()
        y_input.setRange(0.0, 1.0)
        y_input.setDecimals(4)
        self.strategy_table.setCellWidget(row, 2, x_input)
        self.strategy_table.setCellWidget(row, 3, y_input)

        def _apply_defaults() -> None:
            current_sid = strategy_combo.currentText().strip()
            dx, dy = self._strategy_param_defaults(current_sid)
            x_input.setValue(dx)
            y_input.setValue(dy)

        strategy_combo.currentTextChanged.connect(lambda _text: _apply_defaults())

        if x_pct == 0.0 and y_pct == 0.0:
            _apply_defaults()
        else:
            x_input.setValue(x_pct)
            y_input.setValue(y_pct)

    def remove_strategy_row(self) -> None:
        row = self.strategy_table.currentRow()
        if row >= 0:
            self.strategy_table.removeRow(row)

    def _read_float_item(self, table: QTableWidget, row: int, col: int, field: str) -> float:
        item = table.item(row, col)
        if item is None or not item.text().strip():
            raise ValueError(f"{field} 不能为空")
        return float(item.text().strip())

    def _read_str_item(self, table: QTableWidget, row: int, col: int, field: str) -> str:
        item = table.item(row, col)
        if item is None or not item.text().strip():
            raise ValueError(f"{field} 不能为空")
        return item.text().strip()

    def _read_combo_text(self, table: QTableWidget, row: int, col: int, field: str) -> str:
        widget = table.cellWidget(row, col)
        if not isinstance(widget, QComboBox):
            raise ValueError(f"{field} 读取失败")
        val = widget.currentText().strip()
        if not val:
            raise ValueError(f"{field} 不能为空")
        return val

    def _read_spin_value(self, table: QTableWidget, row: int, col: int, field: str) -> float:
        widget = table.cellWidget(row, col)
        if not isinstance(widget, QDoubleSpinBox):
            raise ValueError(f"{field} 读取失败")
        return float(widget.value())

    def build_config(self) -> PortfolioConfig:
        start_date = pd.Timestamp(self.start_date_text.text().strip())
        end_date = pd.Timestamp(self.end_date_text.text().strip())
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")

        cash_text = self.initial_cash_input.text().strip()
        if not cash_text:
            raise ValueError("初始资金不能为空")
        initial_cash = float(cash_text)
        if initial_cash <= 0:
            raise ValueError("初始资金必须大于0")

        fee_rate = float(self.fee_rate_input.value())

        symbols: list[SymbolSpec] = []
        weights_sum = 0.0
        symbol_set: set[str] = set()

        for row in range(self.symbol_table.rowCount()):
            symbol = self._read_str_item(self.symbol_table, row, 0, "Symbol")
            weight = self._read_float_item(self.symbol_table, row, 1, "Weight")
            if not (symbol.isdigit() and len(symbol) == 6):
                raise ValueError(f"非法Symbol: {symbol}")
            if weight < 0 or weight > 1:
                raise ValueError(f"Weight越界: {symbol}")
            symbols.append(SymbolSpec(symbol=symbol, weight=weight, strategies=[]))
            symbol_set.add(symbol)
            weights_sum += weight

        if not symbols:
            raise ValueError("至少需要一个标的")
        if weights_sum <= 0:
            raise ValueError("权重总和必须大于0")
        if weights_sum > 1.0 + 1e-8:
            raise ValueError("权重总和不能超过1.0")

        symbol_map = {s.symbol: s for s in symbols}

        for row in range(self.strategy_table.rowCount()):
            symbol = self._read_combo_text(self.strategy_table, row, 0, "策略Symbol")
            name = self._read_combo_text(self.strategy_table, row, 1, "策略名")
            x_pct = self._read_spin_value(self.strategy_table, row, 2, "x_pct")
            y_pct = self._read_spin_value(self.strategy_table, row, 3, "y_pct")

            if symbol not in symbol_set:
                raise ValueError(f"策略行中的Symbol未在标的列表中: {symbol}")
            if name not in self.strategy_catalog:
                raise ValueError(f"未知策略: {name}")
            if x_pct < 0 or x_pct > 1 or y_pct < 0 or y_pct > 1:
                raise ValueError(f"x_pct/y_pct 必须在[0,1]: {symbol}/{name}")

            symbol_map[symbol].strategies.append(StrategySpec(name=name, x_pct=x_pct, y_pct=y_pct))

        for spec in symbols:
            if not spec.strategies:
                spec.strategies.append(StrategySpec(name="do_nothing", x_pct=0.0, y_pct=0.0))

        return PortfolioConfig(
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
        )

    def accept(self) -> None:
        try:
            _ = self.build_config()
            super().accept()
        except Exception as exc:
            QMessageBox.warning(self, "配置错误", str(exc))
