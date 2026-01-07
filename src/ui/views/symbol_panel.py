from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from PyQt6 import QtCore, QtGui, QtWidgets

from src.ui.views.ui_utils import make_colored_icon


class SymbolListWidget(QtWidgets.QListWidget):
    """List widget that drags plain text codes for the K-line drop target."""

    def startDrag(self, supported_actions: QtCore.Qt.DropActions) -> None:  # noqa: D401 - Qt override
        items = self.selectedItems()
        if not items:
            return
        code = items[0].text().split()[0].strip()
        mime = QtCore.QMimeData()
        mime.setText(code)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec(QtCore.Qt.DropAction.CopyAction)


class SymbolsPanel(QtWidgets.QWidget):
    def __init__(
        self,
        symbol_map: Dict[str, str],
        name_to_code: Dict[str, str],
        suggestion_list: List[str],
        on_symbol_added: Callable[[str], None],
        on_symbols_deleted: Callable[[list[str]], None],
        on_symbol_view: Callable[[str], None],
        register_tooltip: Callable[[QtWidgets.QWidget, str], None],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.symbol_map = symbol_map
        self.name_to_code = name_to_code
        self.suggestion_list = suggestion_list
        self.on_symbol_added = on_symbol_added
        self.on_symbols_deleted = on_symbols_deleted
        self.on_symbol_view = on_symbol_view
        self.register_tooltip = register_tooltip

        self.symbol_list_widget = SymbolListWidget()
        self.symbol_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.symbol_list_widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.symbol_list_widget.customContextMenuRequested.connect(self._show_symbol_context_menu)
        self.symbol_list_widget.setDragEnabled(True)
        self.symbol_list_widget.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragOnly)
        self.symbol_list_widget.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)
        self.symbol_list_widget.itemDoubleClicked.connect(
            lambda item: self.on_symbol_view(item.text().split()[0])
        )

        self._build_layout()

    def _build_layout(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        label = QtWidgets.QLabel("Symbols")
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        vbox.addWidget(label)

        vbox.addWidget(self.symbol_list_widget)
        vbox.addWidget(self._build_action_buttons())

    def _build_action_buttons(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(bar)
        hbox.setContentsMargins(0, 6, 0, 0)
        hbox.setSpacing(2)
        hbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        buttons = [
            ("Add Symbol", "Add symbol to list", make_colored_icon("add", "#2ecc71")),
            ("Delete Symbol", "Delete selected symbols", make_colored_icon("remove", "#e74c3c")),
        ]
        hbox.addStretch(1)
        for text, tooltip, icon in buttons:
            btn = QtWidgets.QToolButton()
            btn.setIcon(icon)
            btn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.register_tooltip(btn, tooltip)
            btn.setAutoRaise(True)
            btn.setIconSize(QtCore.QSize(26, 26))
            if text == "Add Symbol":
                btn.clicked.connect(self._on_add_symbol)
            elif text == "Delete Symbol":
                btn.clicked.connect(self._on_delete_symbol)
            hbox.addWidget(btn)

        hbox.addStretch(1)
        return bar

    def load_initial_symbols(self, codes: Iterable[str]) -> None:
        for code in codes:
            self.add_symbol_display(code)

    def add_symbol_display(self, code: str) -> bool:
        if self._symbol_exists(code):
            return False
        name = self.symbol_map.get(code, "")
        display = f"{code}  {name}" if name else code
        self.symbol_list_widget.addItem(display)
        return True

    def _symbol_exists(self, code: str) -> bool:
        return any(
            self.symbol_list_widget.item(i).text().startswith(code)
            for i in range(self.symbol_list_widget.count())
        )

    def _on_add_symbol(self) -> None:
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Symbol")
        dialog.resize(220, 140)
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        input_box = QtWidgets.QLineEdit()
        input_box.setPlaceholderText("Search by code or name...")
        completer = QtWidgets.QCompleter(self.suggestion_list, dialog)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        input_box.setCompleter(completer)

        def handle_completion(text: str) -> None:
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
            self.add_symbol_display(code)
            self.on_symbol_added(code)
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
        removed_codes: list[str] = []
        for item in items:
            code = item.text().split()[0].strip().upper()
            row = self.symbol_list_widget.row(item)
            self.symbol_list_widget.takeItem(row)
            if code:
                removed_codes.append(code)
        if removed_codes:
            self.on_symbols_deleted(removed_codes)

    def _show_symbol_context_menu(self, pos: QtCore.QPoint) -> None:
        item = self.symbol_list_widget.itemAt(pos)
        if item is None:
            return
        code = item.text().split()[0]
        menu = QtWidgets.QMenu(self)
        action = menu.addAction("View K-line")
        action.triggered.connect(lambda: self.on_symbol_view(code))
        menu.exec(self.symbol_list_widget.mapToGlobal(pos))

    def _resolve_input_to_code(self, text: str) -> str | None:
        t = text.strip()
        if not t:
            return None
        code_token = t.split()[0].strip().upper()
        if code_token in self.symbol_map:
            return code_token
        if t in self.name_to_code:
            return self.name_to_code[t]
        matches = [
            c
            for c, n in self.symbol_map.items()
            if c.startswith(code_token) or n.startswith(t)
        ]
        if len(matches) == 1:
            return matches[0]
        return None
