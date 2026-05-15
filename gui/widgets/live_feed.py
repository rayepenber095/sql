from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

from core.models import ScanResult


class LiveFeed(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 9, parent)
        self.setHorizontalHeaderLabels(
            ["Time", "Type", "URL", "Parameter", "Category", "Status", "Time(ms)", "Length", "Result"]
        )
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        for i, w in enumerate([80, 60, 220, 100, 120, 60, 80, 70, 100]):
            self.setColumnWidth(i, w)
        self._vuln_only = False
        self._all_results: list[ScanResult] = []

    def add_result(self, result: ScanResult) -> None:
        self._all_results.append(result)
        if self._vuln_only and not result.vulnerable:
            return
        self._insert_row(result)
        self.scrollToBottom()

    def _insert_row(self, result: ScanResult) -> None:
        row = self.rowCount()
        self.insertRow(row)
        short_url = result.url if len(result.url) <= 50 else result.url[:47] + "..."
        values = [
            result.timestamp.strftime("%H:%M:%S"),
            result.vector_type,
            short_url,
            result.parameter,
            result.category,
            str(result.status_code),
            f"{result.response_time_ms:.0f}",
            str(result.response_length),
            result.vuln_type if result.vulnerable else "safe",
        ]
        if result.vulnerable:
            color = QColor(80, 20, 20)
        elif result.status_code == 500:
            color = QColor(60, 50, 10)
        else:
            color = QColor(20, 40, 20)
        bold = QFont()
        bold.setBold(True)
        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item.setBackground(color)
            if result.vulnerable:
                item.setFont(bold)
            self.setItem(row, col, item)

    def set_vuln_only(self, vuln_only: bool) -> None:
        self._vuln_only = vuln_only
        self.setRowCount(0)
        for r in self._all_results:
            if vuln_only and not r.vulnerable:
                continue
            self._insert_row(r)

    def clear_feed(self) -> None:
        self._all_results.clear()
        self.setRowCount(0)

    def get_result_at_row(self, row: int) -> ScanResult | None:
        filtered = [r for r in self._all_results if (r.vulnerable or not self._vuln_only)]
        if row < 0 or row >= len(filtered):
            return None
        return filtered[row]
