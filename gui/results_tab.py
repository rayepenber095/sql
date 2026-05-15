from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import ScanResult
from gui.widgets.live_feed import LiveFeed


class ResultsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        title = QLabel("Live Request Feed")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        toolbar.addWidget(title)
        self.vuln_only_cb = QCheckBox("Show vulnerable only")
        self.vuln_only_cb.stateChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.vuln_only_cb)
        self.clear_btn = QPushButton("Clear")
        toolbar.addWidget(self.clear_btn)
        self.export_btn = QPushButton("Export Selected")
        toolbar.addWidget(self.export_btn)
        toolbar.addStretch(1)
        main.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.live_feed = LiveFeed()
        self.live_feed.itemSelectionChanged.connect(self._on_row_selected)
        splitter.addWidget(self.live_feed)

        lower = QSplitter(Qt.Orientation.Horizontal)
        request_group = QGroupBox("Request")
        request_layout = QVBoxLayout(request_group)
        self.request_box = QTextEdit()
        self.request_box.setReadOnly(True)
        self.request_box.setFont(QFont("Monospace", 9))
        request_layout.addWidget(self.request_box)
        lower.addWidget(request_group)

        response_group = QGroupBox("Response")
        response_layout = QVBoxLayout(response_group)
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setFont(QFont("Monospace", 9))
        response_layout.addWidget(self.response_box)
        lower.addWidget(response_group)
        splitter.addWidget(lower)
        splitter.setSizes([420, 220])
        main.addWidget(splitter)

        self.detail_label = QLabel("")
        main.addWidget(self.detail_label)

        self.clear_btn.clicked.connect(self.clear_feed)

    def add_result(self, result: ScanResult) -> None:
        self.live_feed.add_result(result)

    def _on_row_selected(self) -> None:
        rows = self.live_feed.selectedItems()
        if not rows:
            return
        selected_row = rows[0].row()
        result = self.live_feed.get_result_at_row(selected_row)
        if result is None:
            return
        self._show_detail(result)

    def _show_detail(self, result: ScanResult) -> None:
        if result.vector_type == "form":
            text = f"POST {result.url} HTTP/1.1\n"
            text += "Content-Type: application/x-www-form-urlencoded\n\n"
            text += f"{result.parameter}={result.payload}"
        else:
            text = f"GET {result.url} HTTP/1.1\n"
            text += f"(parameter: {result.parameter} = {result.payload})"
        self.request_box.setPlainText(text)

        self.response_box.setPlainText(f"HTTP/1.1 {result.status_code}\n\n{result.response_body}")

        vuln_text = f"⚠ {result.vuln_type} ({result.confidence})" if result.vulnerable else "✓ Not Vulnerable"
        self.detail_label.setText(
            f"Status: {result.status_code}  |  "
            f"Time: {result.response_time_ms:.0f}ms  |  "
            f"Length: {result.response_length}  |  {vuln_text}"
        )

    def _on_filter_changed(self, state: int) -> None:
        self.live_feed.set_vuln_only(state == Qt.CheckState.Checked.value)

    def clear_feed(self) -> None:
        self.live_feed.clear_feed()
        self.request_box.clear()
        self.response_box.clear()
        self.detail_label.setText("")
