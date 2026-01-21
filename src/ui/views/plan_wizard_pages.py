from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from PyQt6 import QtCore, QtWidgets
from src.ui.views.wizards.pages.factors_page import FactorsPage


class UniversePage(QtWidgets.QWidget):
    def __init__(
        self,
        defaults: Dict[str, Any],
        symbol_map: Dict[str, str],
        name_to_code: Dict[str, str],
        suggestion_list: List[str],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._defaults = defaults.get("Universe", {})
        self.symbol_map = symbol_map
        self.name_to_code = name_to_code
        self.suggestion_list = suggestion_list
        self._build()

    def _build(self) -> None:
        layout = QtWidgets.QFormLayout(self)
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.u_start = QtWidgets.QDateEdit(calendarPopup=True)
        self.u_end = QtWidgets.QDateEdit(calendarPopup=True)
        self.u_start.setDisplayFormat("yyyy-MM-dd")
        self.u_end.setDisplayFormat("yyyy-MM-dd")
        try:
            sd = QtCore.QDate.fromString(self._defaults.get("start_date", ""), "yyyy-MM-dd")
            ed = QtCore.QDate.fromString(self._defaults.get("end_date", ""), "yyyy-MM-dd")
        except Exception:
            sd = QtCore.QDate.currentDate().addYears(-1)
            ed = QtCore.QDate.currentDate()
        self.u_start.setDate(sd if sd.isValid() else QtCore.QDate.currentDate().addYears(-1))
        self.u_end.setDate(ed if ed.isValid() else QtCore.QDate.currentDate())
        layout.addRow("Start Date", self.u_start)
        layout.addRow("End Date", self.u_end)

        self.u_type_static = QtWidgets.QRadioButton("Static List")
        self.u_type_dynamic = QtWidgets.QRadioButton("Dynamic Rule")
        utype = self._defaults.get("type", "static")
        (self.u_type_static if utype == "static" else self.u_type_dynamic).setChecked(True)
        type_box = QtWidgets.QWidget()
        hb = QtWidgets.QHBoxLayout(type_box)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.addWidget(self.u_type_static)
        hb.addWidget(self.u_type_dynamic)
        hb.addStretch(1)
        layout.addRow("Universe Type", type_box)

        self.u_symbols_table = QtWidgets.QTableWidget(0, 2)
        self.u_symbols_table.setHorizontalHeaderLabels(["Symbol", "Initial Shares"])
        self.u_symbols_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.u_symbols_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.u_symbols_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.u_symbols_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.u_symbol_input = QtWidgets.QLineEdit()
        self.u_symbol_input.setPlaceholderText("Search by code or name…")
        completer = QtWidgets.QCompleter(self.suggestion_list, self)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        self.u_symbol_input.setCompleter(completer)
        self.u_symbol_shares = QtWidgets.QSpinBox()
        self.u_symbol_shares.setRange(0, 1_000_000_000)
        self.u_symbol_shares.setValue(0)
        add_btn = QtWidgets.QPushButton("Add")
        del_btn = QtWidgets.QPushButton("Delete Selected")
        add_btn.clicked.connect(self._add_symbol_from_input)
        del_btn.clicked.connect(self._delete_selected)
        controls = QtWidgets.QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.addWidget(self.u_symbol_input, stretch=2)
        controls.addWidget(QtWidgets.QLabel("Shares"))
        controls.addWidget(self.u_symbol_shares)
        controls.addWidget(add_btn)
        controls.addWidget(del_btn)
        symbols_box = QtWidgets.QVBoxLayout()
        symbols_box.setContentsMargins(0, 0, 0, 0)
        symbols_box.setSpacing(4)
        symbols_box.addLayout(controls)
        symbols_box.addWidget(self.u_symbols_table)
        symbols_widget = QtWidgets.QWidget()
        symbols_widget.setLayout(symbols_box)
        # preload from defaults: prefer holdings with shares; fallback to symbols list (shares=0)
        holdings = self._defaults.get("holdings", []) or []
        if not holdings:
            holdings = [{"symbol": s, "shares": 0} for s in self._defaults.get("symbols", [])]
        for entry in holdings:
            sym = entry.get("symbol") or entry.get("code") or ""
            shares = int(entry.get("shares", 0) or 0)
            self._add_symbol_to_list(sym, shares)
        layout.addRow("Symbols", symbols_widget)

        cash_box = QtWidgets.QHBoxLayout()
        cash_box.setContentsMargins(0, 0, 0, 0)
        cash_box.setSpacing(8)
        self.u_cash_daily = QtWidgets.QDoubleSpinBox()
        self.u_cash_daily.setRange(0.0, 1e12)
        self.u_cash_daily.setDecimals(2)
        self.u_cash_daily.setSingleStep(1000)
        self.u_cash_weekly = QtWidgets.QDoubleSpinBox()
        self.u_cash_weekly.setRange(0.0, 1e12)
        self.u_cash_weekly.setDecimals(2)
        self.u_cash_weekly.setSingleStep(1000)
        self.u_cash_monthly = QtWidgets.QDoubleSpinBox()
        self.u_cash_monthly.setRange(0.0, 1e12)
        self.u_cash_monthly.setDecimals(2)
        self.u_cash_monthly.setSingleStep(1000)
        injections = self._defaults.get("cash_injections", {}) or {}
        self.u_cash_daily.setValue(float(injections.get("daily", 0.0)))
        self.u_cash_weekly.setValue(float(injections.get("weekly", 0.0)))
        self.u_cash_monthly.setValue(float(injections.get("monthly", 0.0)))
        cash_box.addWidget(QtWidgets.QLabel("Daily"))
        cash_box.addWidget(self.u_cash_daily)
        cash_box.addWidget(QtWidgets.QLabel("Weekly"))
        cash_box.addWidget(self.u_cash_weekly)
        cash_box.addWidget(QtWidgets.QLabel("Monthly"))
        cash_box.addWidget(self.u_cash_monthly)
        layout.addRow("Cash Injection", cash_box)

        self.u_freq = QtWidgets.QComboBox()
        self.u_freq.addItems(["1d"])
        self.u_freq.setCurrentText(self._defaults.get("data_frequency", "1d"))
        self.u_freq.setEnabled(False)
        layout.addRow("Data Frequency", self.u_freq)

    # --- actions ---
    def _add_symbol_from_input(self) -> None:
        code = self._resolve_input_to_code(self.u_symbol_input.text())
        if not code or code not in self.symbol_map:
            QtWidgets.QMessageBox.warning(self, "Invalid", "请输入有效的标的（代码或名称），仅允许数据库中的股票代码。")
            return
        shares = int(self.u_symbol_shares.value()) if hasattr(self, "u_symbol_shares") else 0
        self._add_symbol_to_list(code, shares)
        self.u_symbol_input.clear()
        if hasattr(self, "u_symbol_shares"):
            self.u_symbol_shares.setValue(0)

    def _delete_selected(self) -> None:
        for rng in self.u_symbols_table.selectedRanges():
            for row in range(rng.bottomRow(), rng.topRow() - 1, -1):
                self.u_symbols_table.removeRow(row)

    def _add_symbol_to_list(self, code: str, shares: int = 0) -> None:
        code_clean = code.strip().upper()
        if not code_clean:
            return
        for i in range(self.u_symbols_table.rowCount()):
            if self.u_symbols_table.item(i, 0) and self.u_symbols_table.item(i, 0).text() == code_clean:
                return
        row = self.u_symbols_table.rowCount()
        self.u_symbols_table.insertRow(row)
        self.u_symbols_table.setItem(row, 0, QtWidgets.QTableWidgetItem(code_clean))
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 1_000_000_000)
        sb.setValue(max(0, int(shares)))
        self.u_symbols_table.setCellWidget(row, 1, sb)

    def _resolve_input_to_code(self, text: str) -> str | None:
        t = text.strip()
        if not t:
            return None
        token = t.split()[0].strip().upper()
        if token in self.symbol_map:
            return token
        if t in self.name_to_code:
            return self.name_to_code[t]
        matches = [c for c, n in self.symbol_map.items() if c.startswith(token) or n.startswith(t)]
        if len(matches) == 1:
            return matches[0]
        return None

    # --- data ---
    def collect(self) -> Dict[str, Any]:
        holdings: list[dict[str, Any]] = []
        for row in range(self.u_symbols_table.rowCount()):
            item = self.u_symbols_table.item(row, 0)
            if not item:
                continue
            code = item.text().strip().upper()
            shares_widget = self.u_symbols_table.cellWidget(row, 1)
            shares_val = 0
            if isinstance(shares_widget, QtWidgets.QSpinBox):
                shares_val = int(shares_widget.value())
            if code:
                holdings.append({"symbol": code, "shares": shares_val})
        symbols = [h["symbol"] for h in holdings]
        return {
            "start_date": self.u_start.date().toString("yyyy-MM-dd"),
            "end_date": self.u_end.date().toString("yyyy-MM-dd"),
            "data_frequency": "1d",
            "type": "static" if self.u_type_static.isChecked() else "dynamic",
            "symbols": symbols,
            "holdings": holdings,
            "cash_injections": {
                "daily": float(self.u_cash_daily.value()),
                "weekly": float(self.u_cash_weekly.value()),
                "monthly": float(self.u_cash_monthly.value()),
            },
        }


class ScoringPage(QtWidgets.QWidget):
    def __init__(self, defaults: Dict[str, Any], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._defaults = defaults.get("Scoring", {})
        self._build()

    def _build(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)

        mode_group = QtWidgets.QGroupBox("Fusion Logic")
        mg = QtWidgets.QVBoxLayout(mode_group)
        self.ar_mode_linear = QtWidgets.QRadioButton("Linear")
        self.ar_mode_cond = QtWidgets.QRadioButton("Conditional")
        self.ar_mode_ai = QtWidgets.QRadioButton("AI Model")
        mg.addWidget(self.ar_mode_linear)
        mg.addWidget(self.ar_mode_cond)
        mg.addWidget(self.ar_mode_ai)
        vbox.addWidget(mode_group)

        self.ar_mode_stack = QtWidgets.QStackedWidget()

        linear_widget = QtWidgets.QWidget()
        lw_layout = QtWidgets.QVBoxLayout(linear_widget)
        self.ar_linear_weights = QtWidgets.QPlainTextEdit()
        self.ar_linear_weights.setPlaceholderText("Enter factor weights as JSON, e.g., {\"MOM_20\": 0.6, \"RSI_14\": 0.4}")
        lw_layout.addWidget(self._wrap_labeled("Weights", self.ar_linear_weights))
        self.ar_mode_stack.addWidget(linear_widget)

        cond_widget = QtWidgets.QWidget()
        cw_layout = QtWidgets.QVBoxLayout(cond_widget)
        self.ar_cond_rule = QtWidgets.QLineEdit()
        self.ar_cond_rule.setPlaceholderText("e.g., index_above_ma20")
        cw_layout.addWidget(self._wrap_labeled("Condition Rule", self.ar_cond_rule))
        self.ar_mode_stack.addWidget(cond_widget)

        ai_widget = QtWidgets.QWidget()
        aw_layout = QtWidgets.QVBoxLayout(ai_widget)
        self.ar_ai_path = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_ai_model)
        aw_layout.addWidget(self._wrap_with_button("Model Path", self.ar_ai_path, browse_btn))
        self.ar_mode_stack.addWidget(ai_widget)

        vbox.addWidget(self.ar_mode_stack)

        sched_group = QtWidgets.QGroupBox("Scheduling / Stasis Field")
        sg = QtWidgets.QFormLayout(sched_group)
        self.ar_freq = QtWidgets.QComboBox()
        self.ar_freq.addItems(["daily", "weekly", "monthly"])
        self.ar_thresh = QtWidgets.QDoubleSpinBox()
        self.ar_thresh.setDecimals(4)
        self.ar_thresh.setRange(0.0, 1.0)
        self.ar_thresh.setSingleStep(0.01)
        sg.addRow("Frequency", self.ar_freq)
        sg.addRow("Rebalance Threshold", self.ar_thresh)
        vbox.addWidget(sched_group)

        cons_group = QtWidgets.QGroupBox("Constraints")
        cg = QtWidgets.QFormLayout(cons_group)
        self.ar_max_pos = QtWidgets.QDoubleSpinBox()
        self.ar_max_pos.setDecimals(2)
        self.ar_max_pos.setRange(0.0, 1.0)
        self.ar_max_pos.setSingleStep(0.05)
        cg.addRow("Max Position per Symbol", self.ar_max_pos)
        vbox.addWidget(cons_group)

        vbox.addStretch(1)

        d = self._defaults
        mode = d.get("fusion_mode", "linear")
        (self.ar_mode_linear if mode == "linear" else self.ar_mode_cond if mode == "conditional" else self.ar_mode_ai).setChecked(True)
        try:
            self.ar_linear_weights.setPlainText(json.dumps(d.get("linear", {}).get("weights", {}), ensure_ascii=False))
        except Exception:
            self.ar_linear_weights.setPlainText("{}")
        self.ar_cond_rule.setText(d.get("conditional", {}).get("rule", ""))
        self.ar_ai_path.setText(d.get("ai", {}).get("model_path", ""))
        self.ar_freq.setCurrentText(d.get("scheduling", {}).get("frequency", "daily"))
        self.ar_thresh.setValue(float(d.get("scheduling", {}).get("rebalance_threshold", 0.05)))
        self.ar_max_pos.setValue(float(d.get("constraints", {}).get("max_position_per_symbol", 0.2)))

        self.ar_mode_linear.toggled.connect(lambda checked: self._set_ar_mode("linear") if checked else None)
        self.ar_mode_cond.toggled.connect(lambda checked: self._set_ar_mode("conditional") if checked else None)
        self.ar_mode_ai.toggled.connect(lambda checked: self._set_ar_mode("ai") if checked else None)
        self._set_ar_mode(mode)

    def _wrap_labeled(self, label: str, widget: QtWidgets.QWidget) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(label)
        v = QtWidgets.QVBoxLayout(box)
        v.setContentsMargins(8, 8, 8, 8)
        v.addWidget(widget)
        return box

    def _wrap_with_button(self, label: str, edit: QtWidgets.QLineEdit, btn: QtWidgets.QPushButton) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox(label)
        h = QtWidgets.QHBoxLayout(box)
        h.setContentsMargins(8, 8, 8, 8)
        h.addWidget(edit)
        h.addWidget(btn)
        return box

    def _browse_ai_model(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select AI Model", "", "Model Files (*.pth *.pt *.onnx);;All Files (*)")
        if path:
            self.ar_ai_path.setText(path)

    def _set_ar_mode(self, mode: str) -> None:
        if mode == "linear":
            self.ar_mode_stack.setCurrentIndex(0)
        elif mode == "conditional":
            self.ar_mode_stack.setCurrentIndex(1)
        else:
            self.ar_mode_stack.setCurrentIndex(2)

    def collect(self) -> Dict[str, Any]:
        mode = "linear" if self.ar_mode_linear.isChecked() else "conditional" if self.ar_mode_cond.isChecked() else "ai"
        try:
            weights = json.loads(self.ar_linear_weights.toPlainText() or "{}")
        except Exception:
            weights = {}
        return {
            "fusion_mode": mode,
            "linear": {"weights": weights},
            "conditional": {"rule": self.ar_cond_rule.text().strip()},
            "ai": {"model_path": self.ar_ai_path.text().strip()},
            "scheduling": {
                "frequency": self.ar_freq.currentText(),
                "rebalance_threshold": float(self.ar_thresh.value()),
            },
            "constraints": {"max_position_per_symbol": float(self.ar_max_pos.value())},
        }


class ExecutionPage(QtWidgets.QWidget):
    def __init__(self, defaults: Dict[str, Any], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._defaults = defaults.get("Execution", {})
        self._build()

    def _build(self) -> None:
        form = QtWidgets.QFormLayout(self)
        d = self._defaults

        self.ex_cash = QtWidgets.QDoubleSpinBox()
        self.ex_cash.setRange(0, 1e12)
        self.ex_cash.setDecimals(2)
        self.ex_cash.setSingleStep(10000)
        self.ex_cash.setValue(float(d.get("initial_cash", 1000000)))
        form.addRow("Initial Cash", self.ex_cash)

        self.ex_comm = QtWidgets.QDoubleSpinBox()
        self.ex_comm.setRange(0.0, 1.0)
        self.ex_comm.setDecimals(6)
        self.ex_comm.setSingleStep(0.0001)
        self.ex_comm.setValue(float(d.get("commission_rate", 0.0003)))
        form.addRow("Commission Rate", self.ex_comm)

        self.ex_tax = QtWidgets.QDoubleSpinBox()
        self.ex_tax.setRange(0.0, 1.0)
        self.ex_tax.setDecimals(6)
        self.ex_tax.setSingleStep(0.0001)
        self.ex_tax.setValue(float(d.get("tax_rate", 0.001)))
        form.addRow("Tax Rate", self.ex_tax)

        self.ex_slip = QtWidgets.QComboBox()
        self.ex_slip.addItems(["Fixed 0.01%", "Volume Weighted"])
        self.ex_slip.setCurrentText(d.get("slippage_model", "Fixed 0.01%"))
        form.addRow("Slippage Model", self.ex_slip)

    def collect(self) -> Dict[str, Any]:
        return {
            "initial_cash": float(self.ex_cash.value()),
            "commission_rate": float(self.ex_comm.value()),
            "tax_rate": float(self.ex_tax.value()),
            "slippage_model": self.ex_slip.currentText(),
        }


class PlanInfoPage(QtWidgets.QWidget):
    def __init__(self, defaults: Dict[str, Any], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._defaults = defaults.get("Metadata", {})
        self._build()

    def _build(self) -> None:
        form = QtWidgets.QFormLayout(self)
        md = self._defaults

        self.md_plan_id = QtWidgets.QLineEdit()
        self.md_plan_id.setPlaceholderText("auto-generate if empty")
        self.md_name = QtWidgets.QLineEdit()
        self.md_name.setPlaceholderText("Plan name")
        self.md_created_at = QtWidgets.QLineEdit()
        self.md_created_at.setPlaceholderText("auto-set on create")
        self.md_desc = QtWidgets.QPlainTextEdit()
        self.md_desc.setPlaceholderText("Describe your plan idea")
        self.md_save_path = QtWidgets.QLineEdit()
        self.md_save_path.setPlaceholderText("Choose a file to save JSON")
        browse = QtWidgets.QPushButton("Browse...")
        browse.clicked.connect(self._browse_save_path)

        self.md_plan_id.setText(md.get("plan_id", ""))
        self.md_name.setText(md.get("name", ""))
        self.md_created_at.setText(md.get("created_at", ""))
        self.md_desc.setPlainText(md.get("description", ""))
        self.md_save_path.setText(md.get("save_path", ""))

        form.addRow("Plan ID", self.md_plan_id)
        form.addRow("Name", self.md_name)
        form.addRow("Created At", self.md_created_at)
        form.addRow("Description", self.md_desc)
        form.addRow("Save Path", self._wrap_with_button_widget(self.md_save_path, browse))

    def _wrap_with_button_widget(self, edit: QtWidgets.QLineEdit, btn: QtWidgets.QPushButton) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit)
        h.addWidget(btn)
        return w

    def _browse_save_path(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Plan JSON", "plan.json", "JSON Files (*.json)")
        if path:
            self.md_save_path.setText(path)

    def collect(self) -> Dict[str, Any]:
        plan_id = self.md_plan_id.text().strip() or str(uuid.uuid4())
        created_at = self.md_created_at.text().strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "plan_id": plan_id,
            "name": self.md_name.text().strip(),
            "created_at": created_at,
            "description": self.md_desc.toPlainText().strip(),
            "save_path": self.md_save_path.text().strip(),
        }


__all__ = [
    "UniversePage",
    "FactorsPage",
    "ScoringPage",
    "ExecutionPage",
    "PlanInfoPage",
]
