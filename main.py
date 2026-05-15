#!/usr/bin/env python3
"""
SQLi Engine — Entry Point
Authorized penetration testing use only.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Create required directories before any imports
Path("db").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)
Path("wordlists").mkdir(exist_ok=True)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SQLi Engine")
    app.setOrganizationName("PenTest Tools")

    # Set platform environment for Kali Linux
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
