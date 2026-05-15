from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SettingsTab(QWidget):
    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        headers_group = QGroupBox("Request Headers")
        headers_form = QFormLayout(headers_group)
        self.ua_input = QLineEdit("Mozilla/5.0 (X11; Linux x86_64)")
        self.accept_input = QLineEdit("text/html,application/json,*/*")
        self.referer_input = QLineEdit()
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("name1=val1; name2=val2")
        headers_form.addRow("User-Agent:", self.ua_input)
        headers_form.addRow("Accept:", self.accept_input)
        headers_form.addRow("Referer:", self.referer_input)
        headers_form.addRow("Custom Cookies:", self.cookies_input)
        layout.addWidget(headers_group)

        proxy_group = QGroupBox("Proxy")
        proxy_form = QFormLayout(proxy_group)
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        self.proxy_cb = QCheckBox()
        proxy_form.addRow("Proxy URL:", self.proxy_input)
        proxy_form.addRow("Enable:", self.proxy_cb)
        layout.addWidget(proxy_group)

        crawl_group = QGroupBox("Crawl Options")
        crawl_form = QFormLayout(crawl_group)
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 10)
        self.depth_spin.setValue(3)
        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(10, 5000)
        self.pages_spin.setValue(200)
        self.robots_cb = QCheckBox()
        crawl_form.addRow("Max Depth:", self.depth_spin)
        crawl_form.addRow("Max Pages:", self.pages_spin)
        crawl_form.addRow("Ignore robots.txt:", self.robots_cb)
        layout.addWidget(crawl_group)

        wordlists_group = QGroupBox("Wordlists")
        wordlists_layout = QHBoxLayout(wordlists_group)
        self.wordlist_path = QLineEdit("wordlists")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_wordlists)
        wordlists_layout.addWidget(self.wordlist_path)
        wordlists_layout.addWidget(browse_btn)
        layout.addWidget(wordlists_group)

        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def get_headers(self) -> dict:
        headers = {"User-Agent": self.ua_input.text()}
        if self.accept_input.text():
            headers["Accept"] = self.accept_input.text()
        if self.referer_input.text():
            headers["Referer"] = self.referer_input.text()
        if self.cookies_input.text():
            headers["Cookie"] = self.cookies_input.text()
        return headers

    def get_proxies(self) -> dict | None:
        if self.proxy_cb.isChecked() and self.proxy_input.text():
            url = self.proxy_input.text()
            return {"http": url, "https": url}
        return None

    def get_wordlists_dir(self) -> str:
        return self.wordlist_path.text() or "wordlists"

    def _browse_wordlists(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Wordlists Directory")
        if path:
            self.wordlist_path.setText(path)

    def _save(self) -> None:
        settings = {
            "headers": self.get_headers(),
            "proxies": self.get_proxies(),
            "wordlists_dir": self.get_wordlists_dir(),
            "max_depth": self.depth_spin.value(),
            "max_pages": self.pages_spin.value(),
        }
        self.settings_saved.emit(settings)
        QMessageBox.information(self, "Settings", "Settings saved.")
