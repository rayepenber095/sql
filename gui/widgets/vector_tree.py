from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.models import SiteMap


class VectorTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Type", "URL / Name", "Method", "Parameters"])
        self.setColumnWidth(0, 90)
        self.setColumnWidth(1, 300)
        self.setColumnWidth(2, 60)
        self.setColumnWidth(3, 200)
        self.setAlternatingRowColors(True)

    def populate(self, site_map: SiteMap) -> None:
        self.clear()
        forms_item = QTreeWidgetItem(["Forms", "", "", ""])
        params_item = QTreeWidgetItem(["Params", "", "", ""])
        cookie_item = QTreeWidgetItem(["Cookies", "", "", ""])

        for item in (forms_item, params_item, cookie_item):
            font = item.font(0)
            font.setBold(True)
            for col in range(4):
                item.setFont(col, font)
            self.addTopLevelItem(item)

        for form in site_map.forms:
            field_names = ", ".join(f.name for f in form.fields)
            child = QTreeWidgetItem(["form", form.url, form.method, field_names])
            bg = QColor(30, 70, 30) if form.method == "GET" else QColor(20, 50, 90)
            for col in range(4):
                child.setBackground(col, bg)
            forms_item.addChild(child)

        for param in site_map.param_vectors:
            child = QTreeWidgetItem(["param", param.url, "GET", param.param_name])
            params_item.addChild(child)

        for cookie in site_map.cookies:
            child = QTreeWidgetItem(["cookie", cookie.url, "-", cookie.name])
            cookie_item.addChild(child)

        forms_item.setText(0, f"Forms ({len(site_map.forms)})")
        params_item.setText(0, f"Params ({len(site_map.param_vectors)})")
        cookie_item.setText(0, f"Cookies ({len(site_map.cookies)})")
        self.expandAll()
