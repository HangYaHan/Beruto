from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any

from PyQt6 import QtCore, QtGui, QtWidgets
import json
import uuid
from datetime import datetime
import csv


class PlanWizardDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Plan Wizard")
        self.resize(960, 640)
        self._defaults = self._load_defaults()
        self._factor_library = self._load_factor_library()
        self._selected_factors: List[Dict[str, Any]] = []
        self._build_ui()

    def _load_defaults(self) -> Dict:
        defaults_path = Path(__file__).resolve().parents[3] / "data" / "plan_defaults.json"
        try:
            with defaults_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "version": 1,
                "Universe": {},
                "Oracle": {},
                "Arbiter": {},
                "Executor": {},
                "Metadata": {},
            }

    def _load_factor_library(self) -> List[Dict[str, Any]]:
        base = Path(__file__).resolve().parents[3] / "data"
        csv_path = base / "factor.csv"
        factors_dir = base / "factors"
        library: List[Dict[str, Any]] = []

        # Built-ins fallback
        builtins = [
            {"name": "Do_Nothing", "params": {"alpha": 0}},
            {"name": "Buy_&_Hold", "params": {"p1": 0, "p2": 0, "p3": 0}},
        ]

        # CSV entries
        if csv_path.exists():
            try:
                with csv_path.open("r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames and "name" in reader.fieldnames:
                        for row in reader:
                            name = (row.get("name") or "").strip()
                            if not name:
                                continue
                            library.append({"name": name, "params": {}})
                    else:
                        for line in csv_path.read_text(encoding="utf-8").splitlines():
                            name = line.strip()
                            if name:
                                library.append({"name": name, "params": {}})
            except Exception:
                pass

        # Merge built-ins
        by_name = {item["name"]: item for item in library}
        for item in builtins:
            by_name.setdefault(item["name"], item)

        # Load param defaults from json files if present
        for name, item in list(by_name.items()):
            json_path = factors_dir / f"{name}.json"
            if json_path.exists():
                try:
                    item["params"] = json.loads(json_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

        return list(by_name.values())

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)

        # Left: vertical navigation of tabs
        self.nav = QtWidgets.QListWidget(splitter)
        self.nav.setFixedWidth(180)
        self.nav.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.nav.setAlternatingRowColors(True)
        for name in ["Universe", "Oracles", "Arbiter", "Executor", "Preserver"]:
            item = QtWidgets.QListWidgetItem(name)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)

        # Right: stacked pages with inputs
        self.pages = QtWidgets.QStackedWidget(splitter)
        self._build_universe_page()
        self._build_oracles_page()
        self._build_arbiter_page()
        self._build_executor_page()
        self._build_preserver_page()

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)

        # Footer buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        self.buttons.accepted.connect(self._on_create)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        # Wire navigation
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)

    # --- Universe Page ---
    def _build_universe_page(self) -> None:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(page)
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Dates
        self.u_start = QtWidgets.QDateEdit(calendarPopup=True)
        self.u_end = QtWidgets.QDateEdit(calendarPopup=True)
        self.u_start.setDisplayFormat("yyyy-MM-dd")
        self.u_end.setDisplayFormat("yyyy-MM-dd")
        try:
            sd = QtCore.QDate.fromString(self._defaults["Universe"]["start_date"], "yyyy-MM-dd")
            ed = QtCore.QDate.fromString(self._defaults["Universe"]["end_date"], "yyyy-MM-dd")
        except Exception:
            sd = QtCore.QDate.currentDate().addYears(-1)
            ed = QtCore.QDate.currentDate()
        self.u_start.setDate(sd if sd.isValid() else QtCore.QDate.currentDate().addYears(-1))
        self.u_end.setDate(ed if ed.isValid() else QtCore.QDate.currentDate())
        layout.addRow("Start Date", self.u_start)
        layout.addRow("End Date", self.u_end)

        # Universe type
        self.u_type_static = QtWidgets.QRadioButton("Static List")
        self.u_type_dynamic = QtWidgets.QRadioButton("Dynamic Rule")
        utype = self._defaults["Universe"].get("type", "static")
        (self.u_type_static if utype == "static" else self.u_type_dynamic).setChecked(True)
        type_box = QtWidgets.QWidget()
        hb = QtWidgets.QHBoxLayout(type_box)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.addWidget(self.u_type_static)
        hb.addWidget(self.u_type_dynamic)
        hb.addStretch(1)
        layout.addRow("Universe Type", type_box)

        # Symbols list with add/remove
        self.u_symbols_list = QtWidgets.QListWidget()
        self.u_symbol_input = QtWidgets.QLineEdit()
        self.u_symbol_input.setPlaceholderText("Add symbol code, e.g., 600519")
        add_btn = QtWidgets.QPushButton("Add")
        del_btn = QtWidgets.QPushButton("Delete Selected")
        add_btn.clicked.connect(self._universe_add_symbol)
        del_btn.clicked.connect(self._universe_delete_symbols)
        controls = QtWidgets.QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.addWidget(self.u_symbol_input)
        controls.addWidget(add_btn)
        controls.addWidget(del_btn)
        symbols_box = QtWidgets.QVBoxLayout()
        symbols_box.setContentsMargins(0, 0, 0, 0)
        symbols_box.addLayout(controls)
        symbols_box.addWidget(self.u_symbols_list)
        symbols_widget = QtWidgets.QWidget()
        symbols_widget.setLayout(symbols_box)
        for s in self._defaults["Universe"].get("symbols", []):
            self._universe_add_symbol_to_list(s)
        layout.addRow("Symbols", symbols_widget)

        # Data frequency (fixed 1d)
        self.u_freq = QtWidgets.QComboBox()
        self.u_freq.addItems(["1d"])
        self.u_freq.setCurrentText(self._defaults["Universe"].get("data_frequency", "1d"))
        self.u_freq.setEnabled(False)
        layout.addRow("Data Frequency", self.u_freq)

        self.pages.addWidget(page)

    # --- Oracles Page ---
    def _build_oracles_page(self) -> None:
        page = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(page)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(8)

        # Search and available factors list
        search_row = QtWidgets.QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        self.factor_search = QtWidgets.QLineEdit()
        self.factor_search.setPlaceholderText("Search factor library...")
        self.factor_search.textChanged.connect(self._filter_factor_library)
        self.factor_available = QtWidgets.QListWidget()
        self.factor_available.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        search_row.addWidget(self.factor_search)
        add_btn = QtWidgets.QPushButton("Add")
        add_btn.clicked.connect(self._add_selected_factor_from_library)
        search_row.addWidget(add_btn)
        vbox.addLayout(search_row)
        vbox.addWidget(self.factor_available, stretch=1)

        # Selected factors and params editor
        selected_group = QtWidgets.QGroupBox("Selected Factors")
        sg_layout = QtWidgets.QVBoxLayout(selected_group)
        self.factor_selected = QtWidgets.QListWidget()
        self.factor_selected.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.factor_selected.currentRowChanged.connect(self._load_selected_factor_params)
        remove_btn = QtWidgets.QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected_factor)
        sel_controls = QtWidgets.QHBoxLayout()
        sel_controls.addStretch(1)
        sel_controls.addWidget(remove_btn)
        sg_layout.addWidget(self.factor_selected)
        sg_layout.addLayout(sel_controls)

        self.factor_params = QtWidgets.QPlainTextEdit()
        self.factor_params.setPlaceholderText("Edit params as JSON for the selected factor")
        sg_layout.addWidget(QtWidgets.QLabel("Parameters (JSON)"))
        sg_layout.addWidget(self.factor_params)
        self.factor_params.textChanged.connect(self._on_params_changed)

        vbox.addWidget(selected_group, stretch=2)

        group_pp = QtWidgets.QGroupBox("Preprocess")
        fl = QtWidgets.QFormLayout(group_pp)
        self.pp_zscore = QtWidgets.QCheckBox("Z-Score Standardization")
        self.pp_missing = QtWidgets.QComboBox(); self.pp_missing.addItems(["none", "ffill", "bfill", "zero"]) 
        fl.addRow(self.pp_zscore)
        fl.addRow("Missing Fill", self.pp_missing)
        vbox.addWidget(group_pp)
        vbox.addStretch(1)

        # Load defaults
        d = self._defaults.get("Oracles", {})
        self._selected_factors = d.get("selected_factors", []) or []
        self.pp_zscore.setChecked(d.get("preprocess", {}).get("zscore", False))
        self.pp_missing.setCurrentText(d.get("preprocess", {}).get("missing_fill", "none"))

        self._refresh_factor_library()
        self._refresh_selected_factors()

        self.pages.addWidget(page)

    # --- Arbiter Page ---
    def _build_arbiter_page(self) -> None:
        page = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(page)

        mode_group = QtWidgets.QGroupBox("Fusion Logic")
        mg = QtWidgets.QVBoxLayout(mode_group)
        self.ar_mode_linear = QtWidgets.QRadioButton("Linear")
        self.ar_mode_cond = QtWidgets.QRadioButton("Conditional")
        self.ar_mode_ai = QtWidgets.QRadioButton("AI Model")
        mg.addWidget(self.ar_mode_linear)
        mg.addWidget(self.ar_mode_cond)
        mg.addWidget(self.ar_mode_ai)
        vbox.addWidget(mode_group)

        # Dynamic section container
        self.ar_mode_stack = QtWidgets.QStackedWidget()

        # Linear weights
        linear_widget = QtWidgets.QWidget()
        lw_layout = QtWidgets.QVBoxLayout(linear_widget)
        self.ar_linear_weights = QtWidgets.QPlainTextEdit()
        self.ar_linear_weights.setPlaceholderText("Enter factor weights as JSON, e.g., {\"MOM_20\": 0.6, \"RSI_14\": 0.4}")
        lw_layout.addWidget(self._wrap_labeled("Weights", self.ar_linear_weights))
        self.ar_mode_stack.addWidget(linear_widget)

        # Conditional rule
        cond_widget = QtWidgets.QWidget()
        cw_layout = QtWidgets.QVBoxLayout(cond_widget)
        self.ar_cond_rule = QtWidgets.QLineEdit()
        self.ar_cond_rule.setPlaceholderText("e.g., index_above_ma20")
        cw_layout.addWidget(self._wrap_labeled("Condition Rule", self.ar_cond_rule))
        self.ar_mode_stack.addWidget(cond_widget)

        # AI model path
        ai_widget = QtWidgets.QWidget()
        aw_layout = QtWidgets.QVBoxLayout(ai_widget)
        self.ar_ai_path = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_ai_model)
        aw_layout.addWidget(self._wrap_with_button("Model Path", self.ar_ai_path, browse_btn))
        self.ar_mode_stack.addWidget(ai_widget)

        vbox.addWidget(self.ar_mode_stack)

        # Scheduling
        sched_group = QtWidgets.QGroupBox("Scheduling / Stasis Field")
        sg = QtWidgets.QFormLayout(sched_group)
        self.ar_freq = QtWidgets.QComboBox(); self.ar_freq.addItems(["daily", "weekly", "monthly"]) 
        self.ar_thresh = QtWidgets.QDoubleSpinBox(); self.ar_thresh.setDecimals(4); self.ar_thresh.setRange(0.0, 1.0); self.ar_thresh.setSingleStep(0.01)
        sg.addRow("Frequency", self.ar_freq)
        sg.addRow("Rebalance Threshold", self.ar_thresh)
        vbox.addWidget(sched_group)

        # Constraints
        cons_group = QtWidgets.QGroupBox("Constraints")
        cg = QtWidgets.QFormLayout(cons_group)
        self.ar_max_pos = QtWidgets.QDoubleSpinBox(); self.ar_max_pos.setDecimals(2); self.ar_max_pos.setRange(0.0, 1.0); self.ar_max_pos.setSingleStep(0.05)
        cg.addRow("Max Position per Symbol", self.ar_max_pos)
        vbox.addWidget(cons_group)

        vbox.addStretch(1)

        # Defaults
        d = self._defaults.get("Arbiter", {})
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

        self.pages.addWidget(page)

    # --- Executor Page ---
    def _build_executor_page(self) -> None:
        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        d = self._defaults.get("Executor", {})

        self.ex_cash = QtWidgets.QDoubleSpinBox(); self.ex_cash.setRange(0, 1e12); self.ex_cash.setDecimals(2); self.ex_cash.setSingleStep(10000)
        self.ex_cash.setValue(float(d.get("initial_cash", 1000000)))
        form.addRow("Initial Cash", self.ex_cash)

        self.ex_comm = QtWidgets.QDoubleSpinBox(); self.ex_comm.setRange(0.0, 1.0); self.ex_comm.setDecimals(6); self.ex_comm.setSingleStep(0.0001)
        self.ex_comm.setValue(float(d.get("commission_rate", 0.0003)))
        form.addRow("Commission Rate", self.ex_comm)

        self.ex_tax = QtWidgets.QDoubleSpinBox(); self.ex_tax.setRange(0.0, 1.0); self.ex_tax.setDecimals(6); self.ex_tax.setSingleStep(0.0001)
        self.ex_tax.setValue(float(d.get("tax_rate", 0.001)))
        form.addRow("Tax Rate", self.ex_tax)

        self.ex_slip = QtWidgets.QComboBox(); self.ex_slip.addItems(["Fixed 0.01%", "Volume Weighted"]) 
        self.ex_slip.setCurrentText(d.get("slippage_model", "Fixed 0.01%"))
        form.addRow("Slippage Model", self.ex_slip)

        self.pages.addWidget(page)

    # --- Preserver / Metadata Page ---
    def _build_preserver_page(self) -> None:
        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        md = self._defaults.get("Metadata", {})

        self.md_plan_id = QtWidgets.QLineEdit(); self.md_plan_id.setPlaceholderText("auto-generate if empty")
        self.md_name = QtWidgets.QLineEdit(); self.md_name.setPlaceholderText("Plan name")
        self.md_created_at = QtWidgets.QLineEdit(); self.md_created_at.setPlaceholderText("auto-set on create")
        self.md_desc = QtWidgets.QPlainTextEdit(); self.md_desc.setPlaceholderText("Describe your plan idea")
        self.md_save_path = QtWidgets.QLineEdit(); self.md_save_path.setPlaceholderText("Choose a file to save JSON")
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

        self.pages.addWidget(page)

    # --- Helpers ---
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

    def _wrap_with_button_widget(self, edit: QtWidgets.QLineEdit, btn: QtWidgets.QPushButton) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit)
        h.addWidget(btn)
        return w

    def _browse_ai_model(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select AI Model", "", "Model Files (*.pth *.pt *.onnx);;All Files (*)")
        if path:
            self.ar_ai_path.setText(path)

    def _browse_save_path(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Plan JSON", "plan.json", "JSON Files (*.json)")
        if path:
            self.md_save_path.setText(path)

    def _universe_add_symbol_to_list(self, code: str) -> None:
        code_clean = code.strip().upper()
        if not code_clean:
            return
        for i in range(self.u_symbols_list.count()):
            if self.u_symbols_list.item(i).text() == code_clean:
                return
        self.u_symbols_list.addItem(code_clean)

    def _universe_add_symbol(self) -> None:
        code = self.u_symbol_input.text()
        self._universe_add_symbol_to_list(code)
        self.u_symbol_input.clear()

    def _universe_delete_symbols(self) -> None:
        for item in self.u_symbols_list.selectedItems():
            row = self.u_symbols_list.row(item)
            self.u_symbols_list.takeItem(row)

    def _refresh_factor_library(self) -> None:
        self.factor_available.clear()
        keyword = self.factor_search.text().strip().lower()
        for item in self._factor_library:
            name = item.get("name", "")
            if keyword and keyword not in name.lower():
                continue
            self.factor_available.addItem(name)

    def _filter_factor_library(self, _: str) -> None:
        self._refresh_factor_library()

    def _add_selected_factor_from_library(self) -> None:
        item = self.factor_available.currentItem()
        if item is None:
            return
        name = item.text()
        existing = {f.get("name") for f in self._selected_factors}
        if name in existing:
            QtWidgets.QMessageBox.information(self, "Duplicate", f"{name} already selected.")
            return
        params = {}
        for lib in self._factor_library:
            if lib.get("name") == name:
                params = json.loads(json.dumps(lib.get("params", {})))
                break
        self._selected_factors.append({"name": name, "params": params})
        self._refresh_selected_factors(select_name=name)

    def _remove_selected_factor(self) -> None:
        row = self.factor_selected.currentRow()
        if row < 0:
            return
        self._selected_factors.pop(row)
        self._refresh_selected_factors()

    def _refresh_selected_factors(self, select_name: str | None = None) -> None:
        self.factor_selected.clear()
        for f in self._selected_factors:
            self.factor_selected.addItem(f.get("name", ""))
        if select_name:
            items = self.factor_selected.findItems(select_name, QtCore.Qt.MatchFlag.MatchExactly)
            if items:
                self.factor_selected.setCurrentItem(items[0])
        elif self._selected_factors:
            self.factor_selected.setCurrentRow(0)
        else:
            self.factor_params.clear()

    def _load_selected_factor_params(self, row: int) -> None:
        if row < 0 or row >= len(self._selected_factors):
            self.factor_params.clear()
            return
        params = self._selected_factors[row].get("params", {})
        try:
            self.factor_params.blockSignals(True)
            self.factor_params.setPlainText(json.dumps(params, ensure_ascii=False, indent=2))
        finally:
            self.factor_params.blockSignals(False)

    def _on_params_changed(self) -> None:
        row = self.factor_selected.currentRow()
        if row < 0 or row >= len(self._selected_factors):
            return
        try:
            params = json.loads(self.factor_params.toPlainText() or "{}")
        except Exception:
            return
        self._selected_factors[row]["params"] = params

    def _set_ar_mode(self, mode: str) -> None:
        if mode == "linear":
            self.ar_mode_stack.setCurrentIndex(0)
        elif mode == "conditional":
            self.ar_mode_stack.setCurrentIndex(1)
        else:
            self.ar_mode_stack.setCurrentIndex(2)

    # --- Create handler ---
    def _on_create(self) -> None:
        plan = self._collect_plan()
        save_path = plan["Metadata"].get("save_path")
        if not save_path:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Plan JSON", "plan.json", "JSON Files (*.json)")
            if not path:
                return
            plan["Metadata"]["save_path"] = path
            save_path = path
        try:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, ensure_ascii=False, indent=2)
            QtWidgets.QMessageBox.information(self, "Saved", f"Plan saved to:\n{save_path}")
            self.accept()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Save Failed", str(exc))

    def _collect_plan(self) -> Dict:
        # Universe
        universe = {
            "start_date": self.u_start.date().toString("yyyy-MM-dd"),
            "end_date": self.u_end.date().toString("yyyy-MM-dd"),
            "data_frequency": "1d",
            "type": "static" if self.u_type_static.isChecked() else "dynamic",
            "symbols": [self.u_symbols_list.item(i).text() for i in range(self.u_symbols_list.count())],
        }

        # Oracles
        oracles = {
            "selected_factors": self._selected_factors,
            "preprocess": {
                "zscore": bool(self.pp_zscore.isChecked()),
                "missing_fill": self.pp_missing.currentText(),
            }
        }

        # Arbiter
        mode = "linear" if self.ar_mode_linear.isChecked() else "conditional" if self.ar_mode_cond.isChecked() else "ai"
        try:
            weights = json.loads(self.ar_linear_weights.toPlainText() or "{}")
        except Exception:
            weights = {}
        arbiter = {
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

        # Executor
        executor = {
            "initial_cash": float(self.ex_cash.value()),
            "commission_rate": float(self.ex_comm.value()),
            "tax_rate": float(self.ex_tax.value()),
            "slippage_model": self.ex_slip.currentText(),
        }

        # Metadata
        plan_id = self.md_plan_id.text().strip() or str(uuid.uuid4())
        created_at = self.md_created_at.text().strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            "plan_id": plan_id,
            "name": self.md_name.text().strip(),
            "created_at": created_at,
            "description": self.md_desc.toPlainText().strip(),
            "save_path": self.md_save_path.text().strip(),
        }

        return {
            "version": int(self._defaults.get("version", 1)),
            "Universe": universe,
            "Oracles": oracles,
            "Arbiter": arbiter,
            "Executor": executor,
            "Metadata": metadata,
        }


__all__ = ["PlanWizardDialog"]
