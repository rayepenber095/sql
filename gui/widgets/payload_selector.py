from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import CATEGORY_DISPLAY_NAMES, CATEGORY_FILE_MAP


class PayloadSelector(QWidget):
    selection_changed = pyqtSignal(list)

    def __init__(self, wordlists_dir: str = "wordlists", parent=None):
        super().__init__(parent)
        self.wordlists_dir = wordlists_dir
        self._checkboxes = {}
        self.preview_combo = None
        self.preview_box = None
        self._keys_in_order = list(CATEGORY_DISPLAY_NAMES.keys())
        self._setup_ui()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        group = QGroupBox("Attack Categories")
        grid = QGridLayout(group)
        defaults = {"union", "error_based", "blind_boolean", "auth_bypass"}
        for i, key in enumerate(self._keys_in_order):
            cb = QCheckBox(CATEGORY_DISPLAY_NAMES[key])
            cb.setChecked(key in defaults)
            cb.stateChanged.connect(self._on_selection_changed)
            self._checkboxes[key] = cb
            grid.addWidget(cb, i // 3, i % 3)
        main.addWidget(group)

        main.addWidget(QLabel("Payload Preview:"))
        self.preview_combo = QComboBox()
        for key in self._keys_in_order:
            self.preview_combo.addItem(CATEGORY_DISPLAY_NAMES[key], key)
        self.preview_combo.currentIndexChanged.connect(self._load_preview)
        main.addWidget(self.preview_combo)

        self.preview_box = QPlainTextEdit()
        self.preview_box.setReadOnly(True)
        self.preview_box.setMaximumHeight(120)
        self.preview_box.setPlaceholderText("Select a category to preview payloads...")
        main.addWidget(self.preview_box)
        self._load_preview(0)

    def get_selected_categories(self) -> list[str]:
        return [k for k, cb in self._checkboxes.items() if cb.isChecked()]

    def _on_selection_changed(self) -> None:
        self.selection_changed.emit(self.get_selected_categories())

    def _load_preview(self, index: int) -> None:
        if index < 0 or index >= self.preview_combo.count():
            self.preview_box.clear()
            return
        category = self.preview_combo.itemData(index)
        filename = CATEGORY_FILE_MAP.get(category, "")
        path = Path(self.wordlists_dir) / filename
        if not path.exists():
            self.preview_box.setPlainText(f"File not found: {path}")
            return
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()[:20]
        self.preview_box.setPlainText("".join(lines).rstrip())
