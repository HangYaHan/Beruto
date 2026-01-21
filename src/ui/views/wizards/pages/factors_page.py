from __future__ import annotations

import json
from typing import Any, Dict, List

from PyQt6 import QtCore, QtWidgets

from src.system.settings import SettingsManager
from pathlib import Path


class FactorCard(QtWidgets.QWidget):
    delete_requested = QtCore.pyqtSignal(QtWidgets.QWidget)

    def __init__(self, factor_metadata: Dict[str, Any], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.factor_metadata = factor_metadata or {}
        self.factor_name = str(self.factor_metadata.get("name", "Factor"))
        self.description = (
            self.factor_metadata.get("description")
            or self.factor_metadata.get("help")
            or ""
        )
        self.param_specs: Dict[str, Any] = self.factor_metadata.get("params", {}) or {}
        self.inputs: Dict[str, QtWidgets.QWidget] = {}
        self._build_ui()

    # --- UI ---
    def _build_ui(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        frame = QtWidgets.QFrame(self)
        frame.setObjectName("factorCard")
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "#factorCard { border: 1px solid #d0d0d0; border-radius: 6px; }"
        )
        vbox = QtWidgets.QVBoxLayout(frame)
        vbox.setContentsMargins(10, 8, 10, 10)
        vbox.setSpacing(6)

        header = QtWidgets.QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        title = QtWidgets.QLabel(self.factor_name)
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        title.setToolTip(self.description)
        header.addWidget(title)

        header.addStretch(1)

        close_btn = QtWidgets.QToolButton()
        close_btn.setText("X")
        close_btn.setAutoRaise(True)
        close_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        close_btn.setToolTip("Remove this factor")
        header.addWidget(close_btn)

        vbox.addLayout(header)

        if self.description:
            desc = QtWidgets.QLabel(self.description)
            desc.setStyleSheet("color: #555; font-size: 11px;")
            desc.setWordWrap(True)
            vbox.addWidget(desc)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)

        for param_name, raw_spec in self.param_specs.items():
            editor = self._create_editor(param_name, raw_spec)
            form.addRow(param_name, editor)
            self.inputs[param_name] = editor

        if not self.param_specs:
            placeholder = QtWidgets.QLabel("No parameters.")
            placeholder.setStyleSheet("color: #777;")
            vbox.addWidget(placeholder)
        else:
            vbox.addLayout(form)

        outer.addWidget(frame)

    # --- helpers ---
    def _normalize_spec(self, raw: Any) -> Dict[str, Any]:
        spec: Dict[str, Any] = {
            "default": raw,
            "type": None,
            "choices": None,
            "min": None,
            "max": None,
            "description": "",
        }
        if isinstance(raw, dict):
            spec.update({
                "default": raw.get("default", raw.get("value")),
                "type": raw.get("type"),
                "choices": raw.get("choices"),
                "min": raw.get("min"),
                "max": raw.get("max"),
                "description": raw.get("description", ""),
            })
        if spec["type"] is None and spec["default"] is not None:
            spec["type"] = type(spec["default"]).__name__
        # Normalize common aliases from settings.json (e.g., "number")
        if isinstance(spec["type"], str):
            typ = spec["type"].lower()
            if typ == "number":
                spec["type"] = "float"
            elif typ in {"str", "string"}:
                spec["type"] = "str"
            elif typ in {"int", "integer"}:
                spec["type"] = "int"
        return spec

    def _create_editor(self, name: str, raw: Any) -> QtWidgets.QWidget:
        spec = self._normalize_spec(raw)
        default = spec["default"]
        ptype = (spec["type"] or "").lower()
        choices = spec["choices"] if isinstance(spec.get("choices"), list) else None
        minimum = spec.get("min")
        maximum = spec.get("max")
        desc = spec.get("description") or ""

        # bool check must precede int (bool is subclass of int)
        if isinstance(default, bool) or ptype == "bool":
            widget: QtWidgets.QWidget = QtWidgets.QCheckBox()
            widget.setChecked(bool(default))
        elif isinstance(default, int) and not isinstance(default, bool) or ptype in {"int", "integer"}:
            sb = QtWidgets.QSpinBox()
            sb.setRange(int(minimum if minimum is not None else -1_000_000_000), int(maximum if maximum is not None else 1_000_000_000))
            sb.setValue(int(default) if default is not None else 0)
            widget = sb
        elif isinstance(default, float) or ptype in {"float", "double", "number"}:
            dsb = QtWidgets.QDoubleSpinBox()
            dsb.setDecimals(6)
            dsb.setRange(float(minimum if minimum is not None else -1e9), float(maximum if maximum is not None else 1e9))
            dsb.setSingleStep(0.01)
            dsb.setValue(float(default) if default is not None else 0.0)
            widget = dsb
        elif choices:
            combo = QtWidgets.QComboBox()
            combo.addItems([str(c) for c in choices])
            if default is not None and str(default) in [str(c) for c in choices]:
                combo.setCurrentText(str(default))
            widget = combo
        else:
            line = QtWidgets.QLineEdit()
            if default is not None:
                line.setText(str(default))
            widget = line

        if desc:
            widget.setToolTip(desc)
        return widget

    # --- data ---
    def get_params(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QtWidgets.QSpinBox):
                params[key] = int(widget.value())
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                params[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QCheckBox):
                params[key] = bool(widget.isChecked())
            elif isinstance(widget, QtWidgets.QComboBox):
                params[key] = widget.currentText()
            elif isinstance(widget, QtWidgets.QLineEdit):
                params[key] = widget.text()
            else:
                params[key] = None
        return params


class FactorsPage(QtWidgets.QWidget):
    def __init__(
        self,
        defaults: Dict[str, Any],
        factor_library: List[Dict[str, Any]],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._defaults = defaults.get("Factors", {})
        self._factor_library = factor_library or []
        self._apply_settings_library()
        if not self._factor_library:
            # Hard fallback: load directly from settings file so local factors always appear
            settings_lib = self._load_factor_schema_from_settings()
            if settings_lib:
                self._factor_library = list(settings_lib.values())
        self._library_by_name: Dict[str, Dict[str, Any]] = {
            (item.get("name") or ""): item for item in self._factor_library if item.get("name")
        }
        self.cards_layout: QtWidgets.QVBoxLayout | None = None
        self.factor_list: QtWidgets.QListWidget | None = None
        self.factor_search: QtWidgets.QLineEdit | None = None
        self.pp_zscore: QtWidgets.QCheckBox | None = None
        self.pp_missing: QtWidgets.QComboBox | None = None
        self._build_ui()
        if not self._factor_library:
            self._load_factors_from_settings_fallback()
        self._refresh_library()
        self._load_defaults()

    def _apply_settings_library(self) -> None:
        """Merge factor definitions from data/settings.json so params are present."""
        settings_lib = self._load_factor_schema_from_settings()
        if not settings_lib:
            return
        if not self._factor_library:
            self._factor_library = list(settings_lib.values())
            return
        updated: list[Dict[str, Any]] = []
        for meta in self._factor_library:
            name = meta.get("name")
            if name and name in settings_lib:
                # Keep existing description but refresh params from settings
                merged = dict(settings_lib[name])
                for k, v in meta.items():
                    if k not in {"params"}:
                        merged.setdefault(k, v)
                updated.append(merged)
            else:
                updated.append(meta)
        self._factor_library = updated

    def _load_factor_schema_from_settings(self) -> Dict[str, Dict[str, Any]]:
        try:
            settings_path = Path(__file__).resolve().parents[5] / "data" / "settings.json"
            payload = json.loads(settings_path.read_text(encoding="utf-8"))
            factors = payload.get("factors", {}) if isinstance(payload, dict) else {}
            lib: Dict[str, Dict[str, Any]] = {}
            for name, meta in factors.items():
                if not name:
                    continue
                entry: Dict[str, Any] = {"name": name}
                if isinstance(meta, dict):
                    if "description" in meta:
                        entry["description"] = meta.get("description") or meta.get("help") or ""
                    if "help" in meta and not entry.get("description"):
                        entry["description"] = meta.get("help") or ""
                    entry["params"] = meta.get("params", {}) or {}
                lib[name] = entry
            return lib
        except Exception:
            return {}

    def _load_factors_from_settings_fallback(self) -> None:
        try:
            project_root = Path(__file__).resolve().parents[5]
            settings = SettingsManager(project_root=project_root)
            factors = getattr(settings, "settings", None).factors if hasattr(settings, "settings") else {}
            if isinstance(factors, dict):
                self._factor_library = []
                for name, meta in factors.items():
                    if not name:
                        continue
                    entry: Dict[str, Any] = {"name": name, "params": {}}
                    if isinstance(meta, dict):
                        entry["params"] = meta.get("params", {}) or {}
                        desc = meta.get("description") or meta.get("help") or ""
                        if desc:
                            entry["description"] = desc
                    self._factor_library.append(entry)
                self._library_by_name = {item["name"]: item for item in self._factor_library if item.get("name")}
        except Exception:
            pass

    # --- UI ---
    def _build_ui(self) -> None:
        main = QtWidgets.QHBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(12)

        left = self._build_library_panel()
        right = self._build_pipeline_panel()

        main.addWidget(left, stretch=3)
        main.addWidget(right, stretch=7)

    def _build_library_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(panel)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(6)

        self.factor_search = QtWidgets.QLineEdit()
        self.factor_search.setPlaceholderText("Search factors...")
        self.factor_search.textChanged.connect(self._refresh_library)
        vbox.addWidget(self.factor_search)

        self.factor_list = QtWidgets.QListWidget()
        self.factor_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.factor_list.itemDoubleClicked.connect(self._handle_add_from_library)
        vbox.addWidget(self.factor_list, stretch=1)

        return panel

    def _build_pipeline_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(panel)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(8)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        self.cards_layout = QtWidgets.QVBoxLayout(container)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch(1)
        scroll.setWidget(container)

        vbox.addWidget(scroll, stretch=1)

        group_pp = QtWidgets.QGroupBox("Preprocess")
        fl = QtWidgets.QFormLayout(group_pp)
        self.pp_zscore = QtWidgets.QCheckBox("Z-Score Standardization")
        self.pp_missing = QtWidgets.QComboBox()
        self.pp_missing.addItems(["none", "ffill", "bfill", "zero"])
        fl.addRow(self.pp_zscore)
        fl.addRow("Missing Fill", self.pp_missing)
        vbox.addWidget(group_pp)

        d = self._defaults.get("preprocess", {})
        self.pp_zscore.setChecked(bool(d.get("zscore", False)))
        self.pp_missing.setCurrentText(str(d.get("missing_fill", "none")))

        return panel

    # --- library ---
    def _refresh_library(self) -> None:
        # QListWidget.__bool__ returns False when empty; guard explicitly for None
        if self.factor_list is None:
            return
        keyword = (self.factor_search.text() if self.factor_search else "").strip().lower()
        self.factor_list.clear()
        for meta in self._factor_library:
            name = meta.get("name", "")
            if keyword and keyword not in name.lower():
                continue
            item = QtWidgets.QListWidgetItem(name)
            desc = meta.get("description") or meta.get("help") or ""
            if desc:
                item.setToolTip(desc)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, meta)
            self.factor_list.addItem(item)

    def _handle_add_from_library(self, item: QtWidgets.QListWidgetItem) -> None:
        meta = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(meta, dict):
            return
        self._add_factor_card(self._clone_metadata(meta))

    # --- pipeline ---
    def _clone_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        copied = json.loads(json.dumps(meta)) if meta else {}
        copied.setdefault("params", {})
        return copied

    def _add_factor_card(self, meta: Dict[str, Any]) -> None:
        if not self.cards_layout:
            return
        card = FactorCard(meta, parent=self)
        card.delete_requested.connect(self._remove_card)
        # insert before stretch at end
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _remove_card(self, card: QtWidgets.QWidget) -> None:
        if not self.cards_layout:
            return
        self.cards_layout.removeWidget(card)
        card.setParent(None)
        card.deleteLater()

    def _iter_cards(self) -> List[FactorCard]:
        cards: List[FactorCard] = []
        if not self.cards_layout:
            return cards
        for i in range(self.cards_layout.count()):
            widget = self.cards_layout.itemAt(i).widget()
            if isinstance(widget, FactorCard):
                cards.append(widget)
        return cards

    def _load_defaults(self) -> None:
        selected = self._defaults.get("selected_factors", []) or []
        for entry in selected:
            name = entry.get("name")
            if not name:
                continue
            meta = self._clone_metadata(self._library_by_name.get(name, {"name": name}))
            params = meta.get("params", {}) or {}
            for k, v in (entry.get("params", {}) or {}).items():
                params[k] = v
            meta["params"] = params
            self._add_factor_card(meta)

    # --- data ---
    def collect(self) -> Dict[str, Any]:
        factors: List[Dict[str, Any]] = []
        for card in self._iter_cards():
            factors.append({"name": card.factor_name, "params": card.get_params()})
        return {
            "selected_factors": factors,
            "preprocess": {
                "zscore": bool(self.pp_zscore.isChecked()) if self.pp_zscore else False,
                "missing_fill": self.pp_missing.currentText() if self.pp_missing else "none",
            },
        }


__all__ = ["FactorsPage", "FactorCard"]
