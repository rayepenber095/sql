from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.crawler import CrawlerWorker
from core.history_manager import HistoryManager
from core.models import RateConfig, SiteMap
from gui.widgets.payload_selector import PayloadSelector
from gui.widgets.vector_tree import VectorTree


class ScannerTab(QWidget):
    scan_requested = pyqtSignal(object, dict, object, int)

    def __init__(self, history: HistoryManager, parent=None):
        super().__init__(parent)
        self.history = history
        self._site_map = None
        self._crawler = None
        self._session_id = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        target_group = QGroupBox("Target")
        target_layout = QHBoxLayout(target_group)
        target_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://target.com")
        target_layout.addWidget(self.url_input)
        self.crawl_btn = QPushButton("🌐 Crawl Site")
        self.crawl_btn.clicked.connect(self._start_crawl)
        target_layout.addWidget(self.crawl_btn)
        main_layout.addWidget(target_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        vectors_group = QGroupBox("Discovered Input Vectors")
        vectors_layout = QVBoxLayout(vectors_group)
        self.vector_tree = VectorTree()
        vectors_layout.addWidget(self.vector_tree)
        splitter.addWidget(vectors_group)

        attack_group = QGroupBox("Attack Configuration")
        attack_layout = QVBoxLayout(attack_group)
        self.payload_selector = PayloadSelector()
        attack_layout.addWidget(self.payload_selector)
        splitter.addWidget(attack_group)
        splitter.setSizes([700, 500])
        main_layout.addWidget(splitter)

        rate_group = QGroupBox("Rate Control")
        rate_layout = QGridLayout(rate_group)
        rate_layout.addWidget(QLabel("Threads:"), 0, 0)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 50)
        self.threads_spin.setValue(10)
        rate_layout.addWidget(self.threads_spin, 0, 1)
        rate_layout.addWidget(QLabel("Req/Sec:"), 1, 0)
        self.rps_spin = QDoubleSpinBox()
        self.rps_spin.setRange(0.1, 50)
        self.rps_spin.setValue(5.0)
        rate_layout.addWidget(self.rps_spin, 1, 1)
        rate_layout.addWidget(QLabel("Max Reqs:"), 2, 0)
        self.maxreqs_spin = QSpinBox()
        self.maxreqs_spin.setRange(0, 999999)
        self.maxreqs_spin.setValue(0)
        rate_layout.addWidget(self.maxreqs_spin, 2, 1)
        rate_layout.addWidget(QLabel("(0 = unlimited)"), 2, 2)
        rate_layout.addWidget(QLabel("Timeout(s):"), 3, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        rate_layout.addWidget(self.timeout_spin, 3, 1)
        main_layout.addWidget(rate_group)

        self.crawl_status = QLabel("Enter a URL and click Crawl Site to begin.")
        main_layout.addWidget(self.crawl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        main_layout.addWidget(self.progress_label)

        buttons = QHBoxLayout()
        self.start_btn = QPushButton("▶  Start Scan")
        self.pause_btn = QPushButton("⏸  Pause")
        self.stop_btn = QPushButton("⏹  Stop")
        self.vuln_label = QLabel("Vulnerabilities found: 0")
        self.start_btn.clicked.connect(self._emit_scan_request)
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.pause_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.vuln_label)
        main_layout.addLayout(buttons)

    def _start_crawl(self) -> None:
        target = self.url_input.text().strip()
        if not target or not (target.startswith("http://") or target.startswith("https://")):
            self.crawl_status.setText("Invalid URL. Use http:// or https://")
            return
        self._crawler = CrawlerWorker(target_url=target, max_depth=3, headers={"User-Agent": "Mozilla/5.0"})
        self._crawler.page_found.connect(self._on_page_found)
        self._crawler.vector_found.connect(self._on_vector_found)
        self._crawler.crawl_complete.connect(self._on_crawl_complete)
        self._crawler.crawl_error.connect(self._on_crawl_error)
        self._crawler.progress.connect(self._on_crawl_progress)
        self.crawl_btn.setEnabled(False)
        self.crawl_status.setText("Crawling...")
        self._crawler.start()

    def _on_page_found(self, url: str) -> None:
        self.crawl_status.setText(f"Crawling: {url}")

    def _on_vector_found(self, vtype: str, desc: str) -> None:
        lines = self.crawl_status.text().splitlines()
        lines.append(f"[{vtype}] {desc}")
        self.crawl_status.setText("\n".join(lines[-3:]))

    def _on_crawl_progress(self, visited: int, queued: int) -> None:
        self.crawl_status.setText(f"Crawled {visited} pages | {queued} in queue...")

    def _on_crawl_complete(self, site_map: SiteMap) -> None:
        self._site_map = site_map
        self.vector_tree.populate(site_map)
        self.start_btn.setEnabled(True)
        self.crawl_btn.setEnabled(True)
        self.crawl_status.setText(
            f"Crawl complete: {len(site_map.pages)} pages, "
            f"{len(site_map.forms)} forms, "
            f"{len(site_map.param_vectors)} params, "
            f"{len(site_map.cookies)} cookies discovered."
        )

    def _on_crawl_error(self, message: str) -> None:
        self.crawl_status.setText(f"Crawl error: {message}")
        self.crawl_btn.setEnabled(True)

    def _emit_scan_request(self) -> None:
        if self._site_map is None:
            self.crawl_status.setText("Crawl a target first.")
            return
        selected_categories = self.payload_selector.get_selected_categories()
        if not selected_categories:
            self.crawl_status.setText("Select at least one payload category.")
            return
        from core.injector import load_payloads

        payloads = load_payloads(selected_categories)
        if not any(payloads.get(cat) for cat in selected_categories):
            self.crawl_status.setText("No payloads loaded from selected categories.")
            return
        rate_config = RateConfig(
            requests_per_second=self.rps_spin.value(),
            max_threads=self.threads_spin.value(),
            request_timeout_sec=self.timeout_spin.value(),
            max_total_requests=self.maxreqs_spin.value(),
        )
        self._session_id = self.history.create_session(self.url_input.text().strip())
        self.scan_requested.emit(self._site_map, payloads, rate_config, self._session_id)

    def update_progress(self, done: int, total: int) -> None:
        self.progress_bar.setVisible(True)
        if total > 0:
            pct = int((done / total) * 100)
            self.progress_bar.setValue(pct)
        self.progress_label.setText(f"{done} / {total} requests")

    def update_vuln_count(self, count: int) -> None:
        self.vuln_label.setText(f"Vulnerabilities found: {count} 🔴" if count > 0 else "Vulnerabilities found: 0")

    def set_scanning(self, scanning: bool) -> None:
        self.start_btn.setEnabled(not scanning)
        self.pause_btn.setEnabled(scanning)
        self.stop_btn.setEnabled(scanning)
        self.crawl_btn.setEnabled(not scanning)
