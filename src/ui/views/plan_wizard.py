from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from PyQt6 import QtCore, QtWidgets

from src.system.settings import SettingsManager
from src.ui.services.factor_service import FactorLibraryLoader
from src.ui.services.plan_storage import PLAN_SIGNATURE, PlanDefaultsLoader, PlanStorage, PlanValidationError
from src.ui.services.symbol_service import SymbolDataService
from src.ui.views.plan_wizard_pages import (
    ArbiterPage,
    ExecutorPage,
    OraclesPage,
    PreserverPage,
    UniversePage,
)


class PlanWizardDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Plan Wizard")
        self.resize(960, 640)
        self.created_plan_path: str | None = None

        project_root = Path(__file__).resolve().parents[3]
        self.settings = SettingsManager(project_root=project_root)
        self.symbol_service = SymbolDataService(project_root, self.settings)
        self.plan_storage = PlanStorage()

        defaults_loader = PlanDefaultsLoader(project_root)
        self._defaults = defaults_loader.load()
        factor_loader = FactorLibraryLoader(project_root, self.settings)
        factor_library = factor_loader.load()
        symbol_map = self.symbol_service.load_symbol_map(allow_fetch=False)
        name_to_code = {name: code for code, name in symbol_map.items()}
        suggestion_list = [f"{code} {name}" for code, name in symbol_map.items()]

        self._build_ui(symbol_map, name_to_code, suggestion_list, factor_library)

    def _build_ui(
        self,
        symbol_map: Dict[str, str],
        name_to_code: Dict[str, str],
        suggestion_list: list[str],
        factor_library: list[Dict[str, Any]],
    ) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)

        self.nav = QtWidgets.QListWidget(splitter)
        self.nav.setFixedWidth(180)
        self.nav.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.nav.setAlternatingRowColors(True)
        for name in ["Universe", "Oracles", "Arbiter", "Executor", "Preserver"]:
            item = QtWidgets.QListWidgetItem(name)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)

        self.pages = QtWidgets.QStackedWidget(splitter)
        self.page_universe = UniversePage(self._defaults, symbol_map, name_to_code, suggestion_list, parent=self.pages)
        self.page_oracles = OraclesPage(self._defaults, factor_library, parent=self.pages)
        self.page_arbiter = ArbiterPage(self._defaults, parent=self.pages)
        self.page_executor = ExecutorPage(self._defaults, parent=self.pages)
        self.page_preserver = PreserverPage(self._defaults, parent=self.pages)
        for page in (
            self.page_universe,
            self.page_oracles,
            self.page_arbiter,
            self.page_executor,
            self.page_preserver,
        ):
            self.pages.addWidget(page)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        self.buttons.accepted.connect(self._on_create)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)

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
            self.plan_storage.save(plan, Path(save_path))
            QtWidgets.QMessageBox.information(self, "Saved", f"Plan saved to:\n{save_path}")
            self.created_plan_path = save_path
            self.accept()
        except PlanValidationError as exc:
            QtWidgets.QMessageBox.warning(self, "Save Failed", str(exc))
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Save Failed", str(exc))

    def _collect_plan(self) -> Dict[str, Any]:
        plan = {
            "signature": PLAN_SIGNATURE,
            "version": int(self._defaults.get("version", 1)),
            "Universe": self.page_universe.collect(),
            "Oracles": self.page_oracles.collect(),
            "Arbiter": self.page_arbiter.collect(),
            "Executor": self.page_executor.collect(),
            "Metadata": self.page_preserver.collect(),
        }
        self.plan_storage.ensure_signature(plan)
        return plan


__all__ = ["PlanWizardDialog", "PLAN_SIGNATURE"]
