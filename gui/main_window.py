from PyQt6.QtWidgets import QLabel, QMainWindow, QStatusBar, QTabWidget

from core.history_manager import HistoryManager
from core.injector import InjectorWorker
from core.models import RateConfig, SiteMap
from gui.history_tab import HistoryTab
from gui.results_tab import ResultsTab
from gui.scanner_tab import ScannerTab
from gui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLi Engine v1.0 — Authorized Testing Only")
        self.setMinimumSize(1200, 750)
        self._injector = None
        self._vuln_count = 0
        self._setup()

    def _setup(self) -> None:
        self._history = HistoryManager("db/history.sqlite")
        self._scanner = ScannerTab(self._history)
        self._results = ResultsTab()
        self._history_tab = HistoryTab(self._history)
        self._settings = SettingsTab()

        tabs = QTabWidget()
        tabs.addTab(self._scanner, "🔍 Scanner")
        tabs.addTab(self._results, "📡 Live Results")
        tabs.addTab(self._history_tab, "📁 History")
        tabs.addTab(self._settings, "⚙ Settings")
        self.setCentralWidget(tabs)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_label = QLabel("Ready.")
        self._status.addWidget(self._status_label)

        self._scanner.scan_requested.connect(self._start_scan)
        self._scanner.pause_btn.clicked.connect(self._pause_scan)
        self._scanner.stop_btn.clicked.connect(self._stop_scan)

        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet(
            """
QMainWindow, QWidget {
  background-color: #0d1117;
  color: #e6edf3;
  font-family: 'Segoe UI', sans-serif;
  font-size: 13px;
}
QTabWidget::pane { border: 1px solid #30363d; }
QTabBar::tab {
  background: #161b22; color: #8b949e;
  padding: 8px 16px; border: 1px solid #30363d;
}
QTabBar::tab:selected { background: #21262d; color: #e6edf3; }
QGroupBox {
  border: 1px solid #30363d; border-radius: 4px;
  margin-top: 8px; padding-top: 8px;
}
QGroupBox::title { color: #8b949e; }
QPushButton {
  background: #21262d; color: #e6edf3;
  border: 1px solid #30363d; border-radius: 4px;
  padding: 6px 14px;
}
QPushButton:hover   { background: #30363d; }
QPushButton:pressed { background: #388bfd; }
QPushButton:disabled { color: #484f58; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
  background: #161b22; color: #e6edf3;
  border: 1px solid #30363d; border-radius: 4px;
  padding: 4px;
}
QTableWidget {
  background: #0d1117; color: #e6edf3;
  gridline-color: #21262d;
  selection-background-color: #1f6feb;
}
QHeaderView::section {
  background: #161b22; color: #8b949e;
  border: 1px solid #30363d; padding: 4px;
}
QTreeWidget {
  background: #0d1117; color: #e6edf3;
  border: 1px solid #30363d;
}
QProgressBar {
  background: #21262d; border: 1px solid #30363d;
  border-radius: 4px; text-align: center;
}
QProgressBar::chunk { background: #1f6feb; border-radius: 3px; }
QScrollBar:vertical {
  background: #161b22; width: 10px;
}
QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; }
"""
        )

    def _start_scan(self, site_map: SiteMap, payloads: dict, rate_config: RateConfig, session_id: int) -> None:
        headers = self._settings.get_headers()
        self._injector = InjectorWorker(
            site_map=site_map,
            payloads=payloads,
            rate_config=rate_config,
            headers=headers,
            session_id=session_id,
            history=self._history,
        )
        self._injector.scan_started.connect(
            lambda total: self._status_label.setText(f"Scanning... {total} requests queued")
        )
        self._injector.result_ready.connect(self._on_result)
        self._injector.progress_updated.connect(self._scanner.update_progress)
        self._injector.scan_complete.connect(self._on_scan_complete)
        self._injector.scan_error.connect(lambda msg: self._status_label.setText(f"Error: {msg}"))
        self._vuln_count = 0
        self._results.clear_feed()
        self._scanner.update_vuln_count(0)
        self._scanner.set_scanning(True)
        self._injector.start()

    def _on_result(self, result) -> None:
        self._results.add_result(result)
        if result.vulnerable:
            self._vuln_count += 1
            self._scanner.update_vuln_count(self._vuln_count)

    def _on_scan_complete(self, total: int, vulns: int) -> None:
        self._scanner.set_scanning(False)
        self._history_tab.refresh()
        self._status_label.setText(f"Scan complete. {total} requests sent. {vulns} vulnerabilities found.")

    def _pause_scan(self) -> None:
        if self._injector is not None:
            if self._injector._limiter.is_paused():
                self._injector.resume()
                self._scanner.pause_btn.setText("⏸  Pause")
                self._status_label.setText("Scan resumed.")
            else:
                self._injector.pause()
                self._scanner.pause_btn.setText("▶  Resume")
                self._status_label.setText("Scan paused.")

    def _stop_scan(self) -> None:
        if self._injector is not None:
            self._injector.stop()
            self._scanner.set_scanning(False)
            self._status_label.setText("Scan stopped by user.")
