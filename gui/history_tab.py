from collections import defaultdict

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.history_manager import HistoryManager
from core.models import SessionRow


class HistoryTab(QWidget):
    def __init__(self, history: HistoryManager, parent=None):
        super().__init__(parent)
        self.history = history
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Past Scan Sessions")
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        title.setFont(font)
        layout.addWidget(title)

        self.sessions_table = QTableWidget(0, 6)
        self.sessions_table.setHorizontalHeaderLabels(["ID", "Target URL", "Started", "Ended", "Requests", "Vulns"])
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sessions_table.horizontalHeader().setStretchLastSection(True)
        self.sessions_table.itemSelectionChanged.connect(self._on_session_selected)
        layout.addWidget(self.sessions_table)

        buttons = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_json_btn = QPushButton("Export JSON")
        self.delete_btn = QPushButton("🗑 Delete")
        self.refresh_btn.clicked.connect(self.refresh)
        self.export_csv_btn.clicked.connect(self._export_csv)
        self.export_json_btn.clicked.connect(self._export_json)
        self.delete_btn.clicked.connect(self._delete_session)
        buttons.addWidget(self.refresh_btn)
        buttons.addWidget(self.export_csv_btn)
        buttons.addWidget(self.export_json_btn)
        buttons.addWidget(self.delete_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        summary_group = QGroupBox("Vulnerability Summary")
        summary_layout = QVBoxLayout(summary_group)
        self.summary_table = QTableWidget(0, 4)
        self.summary_table.setHorizontalHeaderLabels(["Vuln Type", "Count", "Confidence", "Parameters"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        summary_layout.addWidget(self.summary_table)
        layout.addWidget(summary_group)

    def refresh(self) -> None:
        sessions = self.history.get_all_sessions()
        self.sessions_table.setRowCount(0)
        for s in sessions:
            row = self.sessions_table.rowCount()
            self.sessions_table.insertRow(row)
            self.sessions_table.setItem(row, 0, QTableWidgetItem(str(s.id)))
            self.sessions_table.setItem(row, 1, QTableWidgetItem(s.target_url))
            self.sessions_table.setItem(row, 2, QTableWidgetItem(s.started_at))
            self.sessions_table.setItem(row, 3, QTableWidgetItem(s.ended_at))
            self.sessions_table.setItem(row, 4, QTableWidgetItem(str(s.total_reqs)))
            vuln_item = QTableWidgetItem(str(s.vulns_found))
            if s.vulns_found > 0:
                vuln_item.setForeground(QColor("red"))
            self.sessions_table.setItem(row, 5, vuln_item)

    def _get_selected_session_id(self) -> int | None:
        rows = self.sessions_table.selectedItems()
        if not rows:
            return None
        return int(self.sessions_table.item(rows[0].row(), 0).text())

    def _on_session_selected(self) -> None:
        sid = self._get_selected_session_id()
        if sid is None:
            return
        results = self.history.get_results_for_session(sid)
        grouped = defaultdict(lambda: {"count": 0, "params": set(), "confidence": set()})
        for r in results:
            if not r.vulnerable:
                continue
            key = r.vuln_type or "Unknown"
            grouped[key]["count"] += 1
            grouped[key]["params"].add(r.parameter)
            if r.confidence:
                grouped[key]["confidence"].add(r.confidence)

        self.summary_table.setRowCount(0)
        for vuln_type, data in grouped.items():
            row = self.summary_table.rowCount()
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(vuln_type))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(data["count"])))
            self.summary_table.setItem(row, 2, QTableWidgetItem(", ".join(sorted(data["confidence"])) or "-"))
            self.summary_table.setItem(row, 3, QTableWidgetItem(", ".join(sorted(data["params"])) or "-"))

    def _export_csv(self) -> None:
        sid = self._get_selected_session_id()
        if sid is None:
            QMessageBox.warning(self, "No Selection", "Select a session first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", f"scan_{sid}.csv", "CSV Files (*.csv)")
        if path:
            self.history.export_to_csv(sid, path)
            QMessageBox.information(self, "Exported", f"Saved to {path}")

    def _export_json(self) -> None:
        sid = self._get_selected_session_id()
        if sid is None:
            QMessageBox.warning(self, "No Selection", "Select a session first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save JSON", f"scan_{sid}.json", "JSON Files (*.json)")
        if path:
            self.history.export_to_json(sid, path)
            QMessageBox.information(self, "Exported", f"Saved to {path}")

    def _delete_session(self) -> None:
        sid = self._get_selected_session_id()
        if sid is None:
            QMessageBox.warning(self, "No Selection", "Select a session first.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete session {sid} and all its results?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history.delete_session(sid)
            self.refresh()
