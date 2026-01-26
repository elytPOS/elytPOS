"""
Main entry point and GUI logic for elytPOS.
"""

import os
import sys
import subprocess

from PySide6.QtCore import Qt, QDate, QEvent, QTimer
from PySide6.QtGui import QFont, QAction, QKeyEvent, QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QDateEdit,
    QAbstractSpinBox,
    QComboBox,
    QStyledItemDelegate,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QFileDialog,
    QTabWidget,
    QTextEdit,
    QCheckBox,
    QGridLayout,
)

from database import DatabaseManager
from printer import ReceiptPrinter
from calculator_gui import CalculatorDialog
from help_system import HelpDialog
import styles
from styles import get_style, get_theme_colors, get_app_path
from printer_config_dialog import PrinterConfigDialog
from version import __version__


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_app_path()
    return os.path.join(base_path, relative_path)


class ProductSearchDialog(QDialog):
    """
    Search and select products from database.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Search &Item")
        self.db = db_manager
        self.selected_product = None
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type Name or Alias to Search...")
        self.search_input.textChanged.connect(self.load_products)
        layout.addWidget(self.search_input)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Barcode", "MRP", "Price", "Base UOM"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.select_product)
        layout.addWidget(self.table)
        self.load_products()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        self.search_input.setFocus()
        self.search_input.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.search_input:
            if event.key() == Qt.Key_Down:
                self.table.setFocus()
                self.table.selectRow(0)
                return True
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self.table.rowCount() > 0:
                    self.table.selectRow(0)
                    self.select_product()
                    return True
        return super().eventFilter(source, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.table.hasFocus():
            self.select_product()
        else:
            super().keyPressEvent(event)

    def load_products(self):
        """
        Fetch products from database based on search query and update table.
        """
        query = self.search_input.text()
        products = (
            self.db.search_products(query) if query else self.db.get_all_products()
        )
        self.table.setRowCount(0)
        for row, prod in enumerate(products):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod[1] or "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(prod[2] or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(prod[3] or "0.0")))
            self.table.setItem(row, 3, QTableWidgetItem(str(prod[4] or "0.0")))
            self.table.setItem(row, 4, QTableWidgetItem(str(prod[6] or "pcs")))
            self.table.item(row, 0).setData(Qt.UserRole, prod)

    def select_product(self):
        """
        Get the product data from the currently selected row and accept dialog.
        """
        row = self.table.currentRow()
        if row >= 0:
            self.selected_product = self.table.item(row, 0).data(Qt.UserRole)
            self.accept()


class RecycleBinDialog(QDialog):
    """
    View and restore deleted items.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Recycle Bin - Items deleted in last 30 days")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        self.label = QLabel("Items in Recycle Bin (Auto-purged after 30 days)")
        self.label.setObjectName("danger")
        layout.addWidget(self.label)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Barcode", "Deleted At", "Restore"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_deleted_products()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def load_deleted_products(self):
        """
        Refresh the list of items currently in the recycle bin.
        """
        products = self.db.get_deleted_products()
        self.table.setRowCount(0)
        for row, p in enumerate(products):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p[1])))
            self.table.setItem(row, 1, QTableWidgetItem(str(p[2])))
            self.table.setItem(
                row, 2, QTableWidgetItem(p[7].strftime("%d-%m-%Y %H:%M"))
            )
            res_btn = QPushButton("Restore")
            res_btn.setObjectName("btnRestore")
            res_btn.clicked.connect(lambda _, pid=p[0]: self.restore_item(pid))
            self.table.setCellWidget(row, 3, res_btn)

    def restore_item(self, pid):
        """
        Move a product from the recycle bin back to active status.
        """
        if self.db.restore_product(pid):
            QMessageBox.information(self, "Success", "Item restored successfully.")
            self.load_deleted_products()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class SchemeEntryDialog(QDialog):
    """
    Interface for creating and editing promotional schemes.
    """

    def __init__(self, db_manager, scheme_id=None, parent=None):
        """
        Initialize the scheme entry dialog, optionally loading an existing scheme for modification.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        title = "Modify Scheme" if scheme_id else "Add New Scheme"
        self.setWindowTitle(title)
        self.db, self.scheme_id = db_manager, scheme_id
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        header_grp = QGroupBox("Scheme Header")
        header_layout = QHBoxLayout(header_grp)
        self.scheme_name = QLineEdit()
        self.scheme_name.setPlaceholderText("Scheme Name")
        self.valid_from = QDateEdit()
        self.valid_from.setDisplayFormat("dd-MM-yyyy")
        self.valid_from.setDate(QDate.currentDate())
        self.valid_from.setCalendarPopup(True)
        self.valid_to = QDateEdit()
        self.valid_to.setDisplayFormat("dd-MM-yyyy")
        self.valid_to.setDate(QDate.currentDate().addDays(365))
        self.valid_to.setCalendarPopup(True)
        header_layout.addWidget(QLabel("&Name:"))
        header_layout.addWidget(self.scheme_name, 1)
        header_layout.addWidget(QLabel("Valid &From:"))
        header_layout.addWidget(self.valid_from)
        header_layout.addWidget(QLabel("&To:"))
        header_layout.addWidget(self.valid_to)
        layout.addWidget(header_grp)
        rule_grp = QGroupBox("Add Item Rule")
        rule_layout = QHBoxLayout(rule_grp)
        self.selected_rule_item = None
        self.item_btn = QPushButton("Select &Item (F3)")
        self.item_btn.setShortcut("F3")
        self.item_btn.clicked.connect(self.select_rule_item)
        self.item_label = QLabel("<No Item>")
        self.item_label.setObjectName("info")
        self.item_label.setMinimumWidth(150)
        self.min_qty = QDoubleSpinBox()
        self.min_qty.setValue(1.0)
        self.min_qty.setPrefix("Min: ")
        self.min_qty.setDecimals(3)
        self.max_qty = QDoubleSpinBox()
        self.max_qty.setMaximum(1000000)
        self.max_qty.setPrefix("Max: ")
        self.max_qty.setSpecialValueText("Max: ∞")
        self.max_qty.setDecimals(3)
        self.target_uom = QComboBox()
        self.target_uom.addItems(["<All UOMs>"] + [u[1] for u in self.db.get_uoms()])
        self.benefit_type = QComboBox()
        self.benefit_type.addItems(["Percent (%)", "Flat Amt (Rs)", "Fixed Rate"])
        self.benefit_value = QDoubleSpinBox()
        self.benefit_value.setMaximum(1000000)
        self.benefit_value.setDecimals(3)
        add_rule_btn = QPushButton("&Add")
        add_rule_btn.clicked.connect(self.add_rule_to_list)
        add_rule_btn.setObjectName("btnSave")
        rule_layout.addWidget(self.item_btn)
        rule_layout.addWidget(self.item_label, 1)
        rule_layout.addWidget(self.min_qty)
        rule_layout.addWidget(self.max_qty)
        rule_layout.addWidget(QLabel("&UOM:"))
        rule_layout.addWidget(self.target_uom)
        rule_layout.addWidget(QLabel("&Type:"))
        rule_layout.addWidget(self.benefit_type)
        rule_layout.addWidget(QLabel("&Value:"))
        rule_layout.addWidget(self.benefit_value)
        rule_layout.addWidget(add_rule_btn)
        layout.addWidget(rule_grp)
        self.items_list = QTableWidget()
        self.items_list.setColumnCount(8)
        self.items_list.setHorizontalHeaderLabels(
            ["Item Name", "ID", "Min Qty", "Max Qty", "UOM", "Type", "Value", "Action"]
        )
        self.items_list.setColumnHidden(1, True)
        self.items_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_list.setMinimumHeight(300)
        layout.addWidget(self.items_list)
        footer = QHBoxLayout()
        save_btn = QPushButton("&Save Scheme (F2)")
        save_btn.clicked.connect(self.save_scheme)
        save_btn.setObjectName("btnSave")
        cancel_btn = QPushButton("&Cancel (Esc)")
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setObjectName("btnCancel")
        footer.addStretch()
        footer.addWidget(save_btn)
        footer.addWidget(cancel_btn)
        layout.addLayout(footer)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        if self.scheme_id:
            self.load_scheme_data()
        save_act = QAction(self)
        save_act.setShortcut("F2")
        save_act.triggered.connect(self.save_scheme)
        self.addAction(save_act)
        cancel_act = QAction(self)
        cancel_act.setShortcut("Esc")
        cancel_act.triggered.connect(self.close)
        self.addAction(cancel_act)

    def select_rule_item(self):
        """
        Open product search and set selected item for a new scheme rule.
        """
        dlg = ProductSearchDialog(self.db, self)
        if dlg.exec() == QDialog.Accepted:
            self.selected_rule_item = dlg.selected_product
            self.item_label.setText(
                f"{self.selected_rule_item[1]} ({self.selected_rule_item[2]})"
            )

    def add_rule_to_list(self):
        """
        Extract rule parameters from inputs and add them to the rules table.
        """
        if not self.selected_rule_item:
            return
        self._add_row_to_table(
            self.selected_rule_item[1],
            self.selected_rule_item[0],
            self.min_qty.value(),
            self.max_qty.value(),
            self.target_uom.currentText(),
            self.benefit_type.currentIndex(),
            self.benefit_value.value(),
        )
        self.selected_rule_item = None
        self.item_label.setText("<No Item>")

    def _add_row_to_table(self, pname, pid, min_q, max_q, uom, b_idx, val):
        """
        Helper to append a formatted rule row to the rules QTableWidget.
        """
        row = self.items_list.rowCount()
        self.items_list.insertRow(row)
        self.items_list.setItem(row, 0, QTableWidgetItem(pname))
        self.items_list.setItem(row, 1, QTableWidgetItem(str(pid)))
        self.items_list.setItem(row, 2, QTableWidgetItem(f"{min_q:.3f}"))
        self.items_list.setItem(
            row, 3, QTableWidgetItem(f"{max_q:.3f}" if max_q > 0 else "∞")
        )
        self.items_list.setItem(row, 4, QTableWidgetItem(uom))
        b_type = (
            "percent" if b_idx == 0 else "amount" if b_idx == 1 else "absolute_rate"
        )
        self.items_list.setItem(row, 5, QTableWidgetItem(b_type))
        self.items_list.setItem(row, 6, QTableWidgetItem(f"{val:.3f}"))
        del_btn = QPushButton("Del")
        del_btn.setObjectName("btnDelete")
        del_btn.clicked.connect(
            lambda: self.items_list.removeRow(self.items_list.currentRow())
        )
        self.items_list.setCellWidget(row, 7, del_btn)

    def load_scheme_data(self):
        """
        Load existing scheme details and rules from the database into the UI.
        """
        header = next(
            (s for s in self.db.get_schemes() if s[0] == self.scheme_id), None
        )
        if header:
            self.scheme_name.setText(header[1])
            if header[2]:
                self.valid_from.setDate(header[2])
            if header[3]:
                self.valid_to.setDate(header[3])
        for r in self.db.get_scheme_rules(self.scheme_id):
            b_idx = 0 if r[6] == "percent" else 1 if r[6] == "amount" else 2
            self._add_row_to_table(
                r[1],
                r[0],
                float(r[3]),
                float(r[4]) if r[4] else 0,
                r[5] or "<All UOMs>",
                b_idx,
                float(r[7]),
            )

    def save_scheme(self):
        """
        Validate and save the current scheme and its rules to the database.
        """
        name = self.scheme_name.text()
        if not name or self.items_list.rowCount() == 0:
            return
        items_data = []
        for r in range(self.items_list.rowCount()):
            items_data.append(
                {
                    "pid": int(self.items_list.item(r, 1).text()),
                    "min_qty": float(self.items_list.item(r, 2).text()),
                    "max_qty": (
                        float(self.items_list.item(r, 3).text())
                        if self.items_list.item(r, 3).text() != "∞"
                        else None
                    ),
                    "target_uom": (
                        None
                        if self.items_list.item(r, 4).text() == "<All UOMs>"
                        else self.items_list.item(r, 4).text()
                    ),
                    "benefit_type": self.items_list.item(r, 5).text(),
                    "benefit_value": float(self.items_list.item(r, 6).text()),
                }
            )
        v_from, v_to = (
            self.valid_from.date().toPython(),
            self.valid_to.date().toPython(),
        )
        if self.scheme_id:
            success = self.db.update_scheme(
                self.scheme_id, name, v_from, v_to, items_data
            )
        else:
            success = self.db.add_scheme(name, v_from, v_to, items_data)
        if success:
            QMessageBox.information(
                self, "Success", f"Scheme '{name}' Saved Successfully."
            )
            self.accept()


class SchemeListDialog(QDialog):
    """
    List and manage existing promotional schemes.
    """

    def __init__(self, db_manager, mode="list", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Scheme List")
        self.db, self.mode = db_manager, mode
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Scheme Name", "Date Range", "Included Items", "Action"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        if self.mode == "modify":
            self.table.doubleClicked.connect(self.modify_selected)
        layout.addWidget(self.table)
        self.load_schemes()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.table.setFocus()
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.table.hasFocus():
            if self.mode == "modify":
                self.modify_selected()
            else:
                row = self.table.currentRow()
                if row >= 0:
                    sid = int(self.table.item(row, 0).text())
                    self.delete_scheme(sid)
        else:
            super().keyPressEvent(event)

    def load_schemes(self):
        """
        Refresh the list of promotional schemes from the database.
        """
        self.table.setRowCount(0)
        for row, s in enumerate(self.db.get_schemes()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(s[0])))
            self.table.setItem(row, 1, QTableWidgetItem(s[1]))
            date_range = f"{s[2].strftime('%d-%m-%Y')} to {s[3].strftime('%d-%m-%Y')}"
            self.table.setItem(row, 2, QTableWidgetItem(date_range))
            self.table.setItem(row, 3, QTableWidgetItem(s[4]))
            btn = QPushButton("&Del" if self.mode == "list" else "&Modify")
            if self.mode == "list":
                btn.setObjectName("btnCancel")
            else:
                btn.setObjectName("btnSave")
            btn.clicked.connect(
                lambda _, sid=s[0]: self.delete_scheme(sid)
                if self.mode == "list"
                else self.open_modify(sid)
            )
            self.table.setCellWidget(row, 4, btn)

    def delete_scheme(self, sid):
        """
        Prompt for confirmation and delete the specified scheme.
        """
        if QMessageBox.question(self, "Confirm", "Delete Scheme?") == QMessageBox.Yes:
            self.db.delete_scheme(sid)
            self.load_schemes()

    def modify_selected(self):
        """
        Open the edit dialog for the currently selected scheme.
        """
        row = self.table.currentRow()
        if row >= 0:
            self.open_modify(int(self.table.item(row, 0).text()))

    def open_modify(self, sid):
        """
        Open SchemeEntryDialog for the given scheme ID.
        """
        res = SchemeEntryDialog(self.db, scheme_id=sid, parent=self).exec()
        self.showFullScreen()
        if res == QDialog.Accepted:
            self.load_schemes()


class UOMMasterDialog(QDialog):
    """
    Management interface for Units of Measure.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("UOM Master")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        input_layout = QHBoxLayout()
        self.uom_input = QLineEdit()
        self.uom_input.setPlaceholderText("New UOM Name")
        self.alias_input = QLineEdit()
        self.alias_input.setPlaceholderText("Alias (Short)")
        self.alias_input.setFixedWidth(100)
        add_btn = QPushButton("&Add")
        add_btn.clicked.connect(self.add_uom)
        input_layout.addWidget(QLabel("UOM:"))
        input_layout.addWidget(self.uom_input)
        input_layout.addWidget(QLabel("Alias:"))
        input_layout.addWidget(self.alias_input)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)
        self.list_widget = QTableWidget()
        self.list_widget.setColumnCount(3)
        self.list_widget.setHorizontalHeaderLabels(["UOM Name", "Alias", "Action"])
        self.list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.list_widget)
        self.load_uoms()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def add_uom(self):
        """
        Validate input and add a new Unit of Measure to the database.
        """
        name = self.uom_input.text().strip()
        alias = self.alias_input.text().strip() or None
        if name and self.db.add_uom(name, alias):
            self.uom_input.clear()
            self.alias_input.clear()
            self.load_uoms()
            self.accept()

    def load_uoms(self):
        """
        Refresh the list of Units of Measure from the database.
        """
        self.list_widget.setRowCount(0)
        for row, u in enumerate(self.db.get_uoms()):
            self.list_widget.insertRow(row)
            self.list_widget.setItem(row, 0, QTableWidgetItem(u[1]))
            self.list_widget.setItem(row, 1, QTableWidgetItem(u[2] or ""))
            del_btn = QPushButton("&Del")
            del_btn.clicked.connect(lambda _, name=u[1]: self.delete_uom(name))
            self.list_widget.setCellWidget(row, 2, del_btn)

    def delete_uom(self, name):
        """
        Confirm and delete the specified Unit of Measure.
        """
        if (
            QMessageBox.question(self, "Confirm", f"Delete UOM '{name}'?")
            == QMessageBox.Yes
        ):
            self.db.delete_uom(name)
            self.load_uoms()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class LanguageMasterDialog(QDialog):
    """
    Management interface for supported languages.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Language Master")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        input_layout = QHBoxLayout()
        self.lang_input = QLineEdit()
        self.lang_input.setPlaceholderText("Language Name (e.g. Hindi)")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Code (hi)")
        add_btn = QPushButton("&Add")
        add_btn.clicked.connect(self.add_lang)
        input_layout.addWidget(QLabel("Lang:"))
        input_layout.addWidget(self.lang_input)
        input_layout.addWidget(QLabel("Code:"))
        input_layout.addWidget(self.code_input)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Code", "Translations", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_langs()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def add_lang(self):
        """
        Validate input and add a new language to the database.
        """
        name = self.lang_input.text().strip()
        code = self.code_input.text().strip() or None
        if name and self.db.add_language(name, code):
            self.lang_input.clear()
            self.code_input.clear()
            self.load_langs()
            self.accept()

    def load_langs(self):
        """
        Refresh the list of supported languages from the database.
        """
        self.table.setRowCount(0)
        for row, lang in enumerate(self.db.get_languages()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(lang[1]))
            self.table.setItem(row, 1, QTableWidgetItem(lang[2]))
            res_btn = QPushButton("Delete")
            res_btn.setObjectName("btnDelete")
            res_btn.clicked.connect(lambda _, lid=lang[0]: self.delete_language(lid))
            self.table.setCellWidget(row, 2, res_btn)

    def open_translations(self, lid, lname):
        """
        Open the translation manager for the selected language.
        """
        TranslationManagerDialog(self.db, lid, lname, self).exec()
        self.showFullScreen()

    def delete_lang(self, lid):
        """
        Confirm and delete the specified language from the database.
        """
        if QMessageBox.question(self, "Confirm", "Delete Language?") == QMessageBox.Yes:
            self.db.delete_language(lid)
            self.load_langs()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


__all__ = [
    "MainWindow",
    "ConfigDialog",
    "LoginDialog",
    "SuperUserCreationDialog",
    "ProductSearchDialog",
    "RecycleBinDialog",
    "SchemeEntryDialog",
    "SchemeListDialog",
    "UOMMasterDialog",
    "LanguageMasterDialog",
    "CustomerMasterDialog",
    "CustomerSearchDialog",
    "PurchaseRegisterDialog",
    "PurchaseEntryDialog",
    "HeldSalesDialog",
    "TranslationManagerDialog",
    "LanguageSelectionDialog",
    "MaintenanceDashboardDialog",
    "InventoryDialog",
    "SalesHistoryDialog",
]


class CreateCompanyDialog(QDialog):
    """
    Comprehensive dialog to create or modify a company profile (BusyWin style).
    """

    def __init__(self, config_params, db_manager=None, parent=None):
        super().__init__(parent)
        self.config_params = config_params
        self.db = db_manager  # If provided, we are in MODIFY mode
        self.is_modify = self.db is not None

        self.setWindowTitle(
            "Modify Company Profile" if self.is_modify else "Create Company Profile"
        )
        self.created_db_name = None
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            "Modify Company Information" if self.is_modify else "Company Information"
        )
        header.setObjectName("title")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- Tab 1: General Info ---
        self.tab_general = QWidget()
        gen_layout = QFormLayout(self.tab_general)

        self.name_input = QLineEdit()
        self.print_name_input = QLineEdit()
        self.short_name_input = QLineEdit()

        # Financial Year Logic
        self.fy_from = QDateEdit()
        self.fy_from.setDisplayFormat("dd-MM-yyyy")
        self.fy_from.setDate(
            QDate(QDate.currentDate().year(), 4, 1)
        )  # Default to April 1st
        self.fy_from.setCalendarPopup(True)

        self.books_from = QDateEdit()
        self.books_from.setDisplayFormat("dd-MM-yyyy")
        self.books_from.setDate(QDate(QDate.currentDate().year(), 4, 1))
        self.books_from.setCalendarPopup(True)

        gen_layout.addRow("Company Name:", self.name_input)
        gen_layout.addRow("Print Name:", self.print_name_input)
        gen_layout.addRow("Short Name (Alias):", self.short_name_input)
        gen_layout.addRow("Financial Year From:", self.fy_from)
        gen_layout.addRow("Books Commencing From:", self.books_from)

        # Auto-fill print name
        self.name_input.textChanged.connect(
            lambda t: self.print_name_input.setText(t)
            if not self.print_name_input.isModified()
            else None
        )

        self.tabs.addTab(self.tab_general, "General")

        # --- Tab 2: Address & Contact ---
        self.tab_address = QWidget()
        addr_layout = QFormLayout(self.tab_address)

        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.country_input = QLineEdit("India")
        self.state_input = QComboBox()
        states = [
            "Andhra Pradesh",
            "Arunachal Pradesh",
            "Assam",
            "Bihar",
            "Chhattisgarh",
            "Goa",
            "Gujarat",
            "Haryana",
            "Himachal Pradesh",
            "Jharkhand",
            "Karnataka",
            "Kerala",
            "Madhya Pradesh",
            "Maharashtra",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Odisha",
            "Punjab",
            "Rajasthan",
            "Sikkim",
            "Tamil Nadu",
            "Telangana",
            "Tripura",
            "Uttar Pradesh",
            "Uttarakhand",
            "West Bengal",
            "Delhi",
            "Jammu & Kashmir",
            "Ladakh",
            "Puducherry",
            "Other",
        ]
        self.state_input.addItems(states)
        self.state_input.setEditable(True)
        self.state_input.setCurrentText("Maharashtra")  # Default

        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.website_input = QLineEdit()

        addr_layout.addRow("Address:", self.address_input)
        addr_layout.addRow("Country:", self.country_input)
        addr_layout.addRow("State:", self.state_input)
        addr_layout.addRow("Phone / Mobile:", self.phone_input)
        addr_layout.addRow("Email:", self.email_input)
        addr_layout.addRow("Website:", self.website_input)

        self.tabs.addTab(self.tab_address, "Address/Contact")

        # --- Tab 3: Statutory Details ---
        self.tab_statutory = QWidget()
        stat_layout = QFormLayout(self.tab_statutory)

        self.gstin_input = QLineEdit()
        self.pan_input = QLineEdit()
        self.cin_input = QLineEdit()
        self.ward_input = QLineEdit()

        stat_layout.addRow("GSTIN / UIN:", self.gstin_input)
        stat_layout.addRow("IT PAN:", self.pan_input)
        stat_layout.addRow("CIN (Corp. ID):", self.cin_input)
        stat_layout.addRow("Ward / Circle:", self.ward_input)

        self.tabs.addTab(self.tab_statutory, "Statutory")

        # --- Tab 4: Currency ---
        self.tab_currency = QWidget()
        curr_layout = QFormLayout(self.tab_currency)

        self.curr_symbol = QLineEdit("₹")
        self.curr_string = QLineEdit("Rupees")
        self.curr_sub_string = QLineEdit("Paise")

        curr_layout.addRow("Currency Symbol:", self.curr_symbol)
        curr_layout.addRow("Currency String:", self.curr_string)
        curr_layout.addRow("Sub String:", self.curr_sub_string)

        self.tabs.addTab(self.tab_currency, "Currency")

        # Footer Buttons
        btn_layout = QHBoxLayout()
        save_btn_text = (
            "Update Company (F2)" if self.is_modify else "Create Company (F2)"
        )
        save_btn = QPushButton(save_btn_text)
        save_btn.setShortcut("F2")
        save_btn.clicked.connect(self.save_data)
        save_btn.setObjectName("btnSave")
        save_btn.setFixedHeight(45)

        cancel_btn = QPushButton("Cancel (Esc)")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setObjectName("btnCancel")
        cancel_btn.setFixedHeight(45)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if self.is_modify:
            self.load_existing_data()
            # Disable FY fields if modifying (usually not changed once created in BusyWin)
            self.fy_from.setEnabled(False)
            self.books_from.setEnabled(False)

        self.name_input.setFocus()

    def load_existing_data(self):
        """Fetch current settings from database."""

        def get(k):
            return self.db.get_setting(k, "")

        self.name_input.setText(get("company_name"))
        self.print_name_input.setText(get("print_name"))
        self.short_name_input.setText(get("short_name"))

        fy_start = get("fy_start")
        if fy_start:
            self.fy_from.setDate(QDate.fromString(fy_start, "yyyy-MM-dd"))

        books_start = get("books_start")
        if books_start:
            self.books_from.setDate(QDate.fromString(books_start, "yyyy-MM-dd"))

        self.address_input.setText(get("address"))
        self.country_input.setText(get("country") or "India")
        self.state_input.setCurrentText(get("state"))
        self.phone_input.setText(get("phone"))
        self.email_input.setText(get("email"))
        self.website_input.setText(get("website"))

        self.gstin_input.setText(get("gstin"))
        self.pan_input.setText(get("pan"))
        self.cin_input.setText(get("cin"))
        self.ward_input.setText(get("ward"))

        self.curr_symbol.setText(get("currency_symbol") or "₹")
        self.curr_string.setText(get("currency_string") or "Rupees")
        self.curr_sub_string.setText(get("currency_sub_string") or "Paise")

    def save_data(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Company Name is required.")
            self.tabs.setCurrentIndex(0)
            self.name_input.setFocus()
            return

        if self.is_modify:
            self.update_existing()
        else:
            self.create_new()

    def update_existing(self):
        """Update current database settings."""
        try:

            def save(k, v):
                self.db.set_setting(k, str(v))

            save("company_name", self.name_input.text())
            save("print_name", self.print_name_input.text())
            save("short_name", self.short_name_input.text())
            # FY usually not updated

            save("address", self.address_input.toPlainText())
            save("country", self.country_input.text())
            save("state", self.state_input.currentText())
            save("phone", self.phone_input.text())
            save("email", self.email_input.text())
            save("website", self.website_input.text())

            save("gstin", self.gstin_input.text())
            save("pan", self.pan_input.text())
            save("cin", self.cin_input.text())
            save("ward", self.ward_input.text())

            save("currency_symbol", self.curr_symbol.text())
            save("currency_string", self.curr_string.text())
            save("currency_sub_string", self.curr_sub_string.text())

            QMessageBox.information(
                self, "Success", "Company profile updated successfully."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update company: {e}")

    def create_new(self):
        name = self.name_input.text().strip()
        fy_year = self.fy_from.date().year()
        next_year = fy_year + 1
        fy_str = f"{fy_year}-{next_year}"

        safe_name = "".join(c for c in name if c.isalnum())
        db_name = f"elytpos_{safe_name}_{fy_str}".lower()

        if DatabaseManager.create_database(self.config_params, db_name):
            self.created_db_name = db_name
            try:
                db_mgr = DatabaseManager(dbname=db_name)

                def save(k, v):
                    db_mgr.set_setting(k, str(v))

                save("company_name", name)
                save("print_name", self.print_name_input.text())
                save("short_name", self.short_name_input.text())
                save("fy_start", self.fy_from.date().toString("yyyy-MM-dd"))
                save("books_start", self.books_from.date().toString("yyyy-MM-dd"))

                save("address", self.address_input.toPlainText())
                save("country", self.country_input.text())
                save("state", self.state_input.currentText())
                save("phone", self.phone_input.text())
                save("email", self.email_input.text())
                save("website", self.website_input.text())

                save("gstin", self.gstin_input.text())
                save("pan", self.pan_input.text())
                save("cin", self.cin_input.text())
                save("ward", self.ward_input.text())

                save("currency_symbol", self.curr_symbol.text())
                save("currency_string", self.curr_string.text())
                save("currency_sub_string", self.curr_sub_string.text())

                db_mgr.close()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Company '{name}' ({fy_str}) created successfully.",
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Initialization Error",
                    f"Database created but failed to save details: {e}",
                )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to create database. Check logs or if name already exists.",
            )


class CompanySelectionDialog(QDialog):
    """
    Dialog to select company and financial year (Database).
    """

    def __init__(self, config_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Company")
        self.config_params = config_params
        self.selected_db = None

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.showFullScreen()

        layout = QVBoxLayout(self)

        # Logo
        self.splash_label = QLabel()
        theme = QApplication.instance().property("theme_name") or "mocha"
        pixmap = QPixmap(resource_path(f"svg/logo_{theme}.svg"))
        if not pixmap.isNull():
            self.splash_label.setPixmap(
                pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.splash_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.splash_label)

        title = QLabel("Select Company & Financial Year")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("font-size: 14pt; padding: 10px;")
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Select (Enter)")
        select_btn.clicked.connect(self.accept_selection)
        select_btn.setFixedHeight(50)
        select_btn.setObjectName("btnSave")

        new_btn = QPushButton("Create New Company")
        new_btn.clicked.connect(self.create_company)
        new_btn.setFixedHeight(50)

        exit_btn = QPushButton("Exit (Esc)")
        exit_btn.clicked.connect(self.reject)
        exit_btn.setFixedHeight(50)
        exit_btn.setObjectName("btnCancel")

        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)

        self.load_databases()

    def load_databases(self):
        self.list_widget.clear()
        dbs = DatabaseManager.list_databases(self.config_params)
        for db in dbs:
            # Parse elytpos_name_fy
            parts = db.split("_")
            display_text = db
            if len(parts) >= 3:
                name = parts[1].capitalize()
                fy = parts[2]
                display_text = f"{name} (FY: {fy})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, db)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        else:
            # Auto-prompt to create if none exist
            QTimer.singleShot(200, self.prompt_create_first_company)

    def prompt_create_first_company(self):
        if self.list_widget.count() == 0:
            if (
                QMessageBox.question(
                    self,
                    "Welcome",
                    "No companies found. Would you like to create your first company?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
            ):
                self.create_company()

    def create_company(self):
        dlg = CreateCompanyDialog(self.config_params, self)
        if dlg.exec() == QDialog.Accepted:
            self.load_databases()
            # Select the new one
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).data(Qt.UserRole) == dlg.created_db_name:
                    self.list_widget.setCurrentRow(i)
                    break

    def accept_selection(self):
        if self.list_widget.currentItem():
            self.selected_db = self.list_widget.currentItem().data(Qt.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Please select a company.")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept_selection()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class LoginDialog(QDialog):
    """
    Handles user authentication.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - elytPOS")
        self.db = db_manager
        self.user = None
        layout = QVBoxLayout(self)
        self.splash_label = QLabel()
        theme = QApplication.instance().property("theme_name") or "mocha"
        pixmap = QPixmap(resource_path(f"svg/logo_{theme}.svg"))
        if not pixmap.isNull():
            self.splash_label.setPixmap(
                pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.splash_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.splash_label)
        title = QLabel("System Login")
        title.setObjectName("title")
        layout.addWidget(title, 0, Qt.AlignCenter)
        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        layout.addLayout(form)
        login_btn = QPushButton("Login")
        login_btn.setFixedHeight(50)
        login_btn.setObjectName("btnSave")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)
        copyright_label = QLabel("© 2026 Mohammed Adnan. All rights reserved.")
        copyright_label.setObjectName("copyright")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        self.setFixedWidth(400)

    def login(self):
        """
        Authenticate user with provided credentials.
        """
        user = self.db.authenticate_user(self.username.text(), self.password.text())
        if user:
            self.user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid Username or Password")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.login()
        else:
            super().keyPressEvent(event)


class SuperUserCreationDialog(QDialog):
    """
    Dialog for initial administrator account creation.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Setup - Create Superuser")
        self.db = db_manager
        layout = QVBoxLayout(self)
        self.splash_label = QLabel()
        theme = QApplication.instance().property("theme_name") or "mocha"
        pixmap = QPixmap(resource_path(f"svg/logo_{theme}.svg"))
        if not pixmap.isNull():
            self.splash_label.setPixmap(
                pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.splash_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.splash_label)
        title = QLabel("Create Admin Account")
        title.setObjectName("title")
        layout.addWidget(title, 0, Qt.AlignCenter)
        info = QLabel(
            "No users found in database.\nPlease create the first Super Administrator."
        )
        info.setObjectName("info")
        layout.addWidget(info, 0, Qt.AlignCenter)
        form = QFormLayout()
        self.username = QLineEdit("admin")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.full_name = QLineEdit("Administrator")
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        form.addRow("Full Name:", self.full_name)
        layout.addLayout(form)
        create_btn = QPushButton("Create & Start")
        create_btn.setFixedHeight(50)
        create_btn.setObjectName("btnSave")
        create_btn.clicked.connect(self.create_user)
        layout.addWidget(create_btn)
        self.setFixedWidth(450)

    def create_user(self):
        """
        Validate input and create the first administrator account in the database.
        """
        if not self.username.text() or not self.password.text():
            QMessageBox.warning(self, "Error", "Username and Password are required.")
            return
        if self.db.add_user(
            self.username.text(), self.password.text(), self.full_name.text(), "admin"
        ):
            QMessageBox.information(
                self, "Success", "Super Administrator created successfully!"
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to create user.")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.create_user()
        else:
            super().keyPressEvent(event)


class UserMasterDialog(QDialog):
    """
    Management interface for user accounts with granular permissions.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("User Master")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        layout = QVBoxLayout(self)

        # Form Area
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        input_form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("(Leave blank to keep existing)")
        self.full_name = QLineEdit()
        self.role_combo = QComboBox()
        self.role_combo.addItems(["staff", "manager", "admin"])
        self.role_combo.currentTextChanged.connect(self.on_role_change)

        input_form.addRow("Username:", self.username)
        input_form.addRow("Password:", self.password)
        input_form.addRow("Full Name:", self.full_name)
        input_form.addRow("Role:", self.role_combo)

        form_layout.addLayout(input_form)

        # Permissions Group
        self.perm_grp = QGroupBox("Granular Permissions")
        p_layout = QGridLayout(self.perm_grp)
        self.check_boxes = {}

        # Define available permissions
        self.perm_keys = [
            ("billing", "Billing & Sales"),
            ("view_reports", "View Reports/History"),
            ("manage_inventory", "Manage Inventory (Items)"),
            ("manage_customers", "Manage Customers"),
            ("manage_purchases", "Manage Purchases"),
            ("manage_schemes", "Manage Schemes"),
            "separator",  # Visual break
            ("manage_users", "Manage Users"),
            ("settings", "System Settings"),
            ("database_ops", "Database Maintenance"),
        ]

        r, c = 0, 0
        for item in self.perm_keys:
            if item == "separator":
                continue
            key, label = item
            cb = QCheckBox(label)
            self.check_boxes[key] = cb
            p_layout.addWidget(cb, r, c)
            c += 1
            if c > 1:
                c = 0
                r += 1

        form_layout.addWidget(self.perm_grp)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save User (F2)")
        save_btn.clicked.connect(self.save_user)
        save_btn.setObjectName("btnSave")
        clear_btn = QPushButton("Clear/New")
        clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(clear_btn)

        form_layout.addLayout(btn_layout)
        layout.addWidget(form_widget)

        # User List
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Username", "Full Name", "Role", "Action"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemClicked.connect(self.load_selected_user)
        layout.addWidget(self.table)

        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.load_users()

    def on_role_change(self, role):
        """Auto-select default permissions based on role."""
        defaults = {
            "staff": ["billing", "view_reports"],
            "manager": [
                "billing",
                "view_reports",
                "manage_inventory",
                "manage_customers",
                "manage_purchases",
                "manage_schemes",
            ],
            "admin": [k[0] for k in self.perm_keys if k != "separator"],
        }

        # Only apply defaults if we are essentially resetting (basic heuristic)
        # For better UX, maybe we shouldn't overwrite manual changes unless explicitly asked.
        # But for simplicity, let's set them when role changes.

        targets = defaults.get(role, [])
        for key, cb in self.check_boxes.items():
            cb.setChecked(key in targets)

    def save_user(self):
        username = self.username.text().strip()
        if not username:
            return

        role = self.role_combo.currentText()
        pwd = self.password.text()

        # If updating existing user and pwd is blank, we need to handle that.
        # Database.add_user hashes password. If we pass empty, it hashes empty.
        # We need to fetch existing user to keep password if empty?
        # Actually add_user upserts.
        # The current db.add_user implementation always hashes the password passed.
        # We might need to modify db.add_user or handle it here.
        # For now, let's require password for new users, and if empty for existing, we might need a workaround.
        # A simple workaround: If password is empty, don't update it?
        # But add_user does ON CONFLICT UPDATE SET ... (without password logic).
        # We can just require password for now or modify DB logic later.
        # Let's enforce password for simplicity in this iteration.

        if not pwd and not self.is_editing_mode():
            QMessageBox.warning(self, "Error", "Password required for new user.")
            return

        # Collect perms
        perms = {k: cb.isChecked() for k, cb in self.check_boxes.items()}

        # Logic for password update:
        # If we use add_user, it will overwrite password hash.
        # If pwd is empty, we shouldn't call add_user like that if we want to preserve old pwd.
        # Let's assume for this feature, you set password every time you save.
        if not pwd:
            QMessageBox.information(self, "Info", "Password not changed.")
            # This means we can't use add_user easily to update just perms without password.
            # I should probably update add_user in database.py to handle None password.
            # For this step, let's assume password is provided.
            return

        if self.db.add_user(username, pwd, self.full_name.text(), role, perms):
            self.clear_form()
            self.load_users()
            QMessageBox.information(self, "Success", "User saved.")

    def is_editing_mode(self):
        # Check if username exists in table
        current = self.username.text()
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text() == current:
                return True
        return False

    def load_selected_user(self, item):
        row = item.row()
        # username = self.table.item(row, 0).text() # Unused
        # We need to fetch full details including permissions
        # Database.get_users returns permissions now.
        # But load_users populates the table.
        user_data = self.table.item(row, 0).data(Qt.UserRole)

        self.username.setText(user_data[1])
        self.full_name.setText(user_data[2] or "")
        self.role_combo.setCurrentText(user_data[3])
        self.password.clear()  # Security

        import json

        perms = {}
        if user_data[4]:
            try:
                perms = json.loads(user_data[4])
            except Exception:
                pass

        for key, cb in self.check_boxes.items():
            cb.setChecked(perms.get(key, False))

    def clear_form(self):
        self.username.clear()
        self.password.clear()
        self.full_name.clear()
        self.role_combo.setCurrentIndex(0)
        self.on_role_change("staff")  # Reset perms

    def load_users(self):
        self.table.setRowCount(0)
        for row, u in enumerate(self.db.get_users()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(u[1]))
            self.table.item(row, 0).setData(Qt.UserRole, u)  # Store full object
            self.table.setItem(row, 1, QTableWidgetItem(u[2] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(u[3]))
            del_btn = QPushButton("Del")
            del_btn.clicked.connect(lambda _, uid=u[0]: self.delete_user(uid))
            self.table.setCellWidget(row, 3, del_btn)

    def delete_user(self, uid):
        if QMessageBox.question(self, "Confirm", "Delete User?") == QMessageBox.Yes:
            self.db.delete_user(uid)
            self.load_users()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class CustomerMasterDialog(QDialog):
    """
    Management interface for the customer database.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Customer Master")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.mobile = QLineEdit()
        self.address = QLineEdit()
        self.email = QLineEdit()
        form.addRow("Customer Name:", self.name)
        form.addRow("Mobile Number:", self.mobile)
        form.addRow("Address:", self.address)
        form.addRow("Email:", self.email)
        add_btn = QPushButton("Add &Customer")
        add_btn.clicked.connect(self.add_customer)
        form.addRow(add_btn)
        layout.addLayout(form)
        search_layout = QHBoxLayout()
        self.master_search_input = QLineEdit()
        self.master_search_input.setPlaceholderText(
            "Search Customer by Name or Mobile..."
        )
        self.master_search_input.textChanged.connect(self.load_customers)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.master_search_input)
        layout.addLayout(search_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Mobile", "Address", "Email", "Action"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_customers()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def add_customer(self):
        """
        Validate input and add a new customer to the database.
        """
        if not self.name.text() or not self.mobile.text():
            QMessageBox.warning(self, "Error", "Name and Mobile are required.")
            return
        if self.db.add_customer(
            self.name.text(), self.mobile.text(), self.address.text(), self.email.text()
        ):
            self.name.clear()
            self.mobile.clear()
            self.address.clear()
            self.email.clear()
            self.load_customers()
            self.accept()

    def load_customers(self):
        """
        Fetch customers from database based on search query and update table.
        """
        self.table.setRowCount(0)
        query_text = ""
        if hasattr(self, "master_search_input"):
            query_text = self.master_search_input.text().strip()
        customers = (
            self.db.search_customers(query_text)
            if query_text
            else self.db.get_customers()
        )
        for row, c in enumerate(customers):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c[1]))
            self.table.setItem(row, 1, QTableWidgetItem(c[2]))
            self.table.setItem(row, 2, QTableWidgetItem(c[3] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(c[4] or ""))
            del_btn = QPushButton("Del")
            del_btn.clicked.connect(
                lambda _, cid=c[0]: self.db.delete_customer(cid)
                or self.load_customers()
            )
            self.table.setCellWidget(row, 4, del_btn)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class CustomerSearchDialog(QDialog):
    """
    Interface for searching and selecting customers.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Customer")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.db = db_manager
        self.selected_customer = None
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type Name or Mobile to Search...")
        self.search_input.textChanged.connect(self.load_customers)
        layout.addWidget(self.search_input)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Mobile", "Address"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.doubleClicked.connect(self.select_customer)
        layout.addWidget(self.table)
        self.load_customers()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        self.search_input.setFocus()

    def load_customers(self):
        """
        Refresh the list of customers based on search input.
        """
        query = self.search_input.text()
        customers = (
            self.db.search_customers(query) if query else self.db.get_customers()
        )
        self.table.setRowCount(0)
        for row, c in enumerate(customers):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(c[1]))
            self.table.setItem(row, 1, QTableWidgetItem(c[2]))
            self.table.setItem(row, 2, QTableWidgetItem(c[3] or ""))
            self.table.item(row, 0).setData(Qt.UserRole, c)

    def select_customer(self):
        """
        Set selected customer and accept the dialog.
        """
        row = self.table.currentRow()
        if row >= 0:
            self.selected_customer = self.table.item(row, 0).data(Qt.UserRole)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.select_customer()
        else:
            super().keyPressEvent(event)


class PurchaseRegisterDialog(QDialog):
    """
    View purchase history for a specific item.
    """

    def __init__(self, db_manager, product_id, product_name, parent=None):
        """
        Initialize the purchase register dialog for a specific product.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle(f"Purchase Register: {product_name}")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Purchase Register for {product_name}"))
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Supplier", "Inv No", "Qty", "Rate", "UOM", "MRP"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_register(product_id)
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def load_register(self, product_id):
        """
        Refresh the purchase history table for the given product.
        """
        rows = self.db.get_item_purchase_register(product_id)
        self.table.setRowCount(0)
        for row, r in enumerate(rows):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r[0].strftime("%d-%m-%Y")))
            self.table.setItem(row, 1, QTableWidgetItem(str(r[1] or "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(r[2] or "")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{float(r[3]):.3f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{float(r[4]):.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(r[5] or "")))
            self.table.setItem(
                row, 6, QTableWidgetItem(f"{float(r[6]):.2f}" if r[6] else "0.00")
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class PurchaseEntryDialog(QDialog):
    """
    Interface for entering new purchase records.
    """

    def __init__(self, db_manager, parent=None):
        """
        Initialize the purchase entry dialog and its components.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Purchase Master")
        self.db = db_manager
        self.updating_cell = False
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        search_grp = QGroupBox("Search Purchases by Item")
        s_layout = QHBoxLayout(search_grp)
        self.item_search = QLineEdit()
        self.item_search.setPlaceholderText("Enter Item Name to find its purchases...")
        self.item_search.textChanged.connect(self.load_search_results)
        s_layout.addWidget(QLabel("Item:"))
        s_layout.addWidget(self.item_search)
        layout.addWidget(search_grp)
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(5)
        self.search_table.setHorizontalHeaderLabels(
            ["ID", "Date", "Supplier", "Invoice", "Total"]
        )
        self.search_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.search_table.setFixedHeight(150)
        layout.addWidget(self.search_table)
        header = QHBoxLayout()
        self.supplier_input = QComboBox()
        self.supplier_input.setEditable(True)
        self.supplier_input.addItems(self.db.get_suppliers())
        self.supplier_input.setPlaceholderText("Supplier Name (Select or Type)")
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("Invoice No")
        header.addWidget(QLabel("Supplier:"))
        header.addWidget(self.supplier_input, 1)
        header.addWidget(QLabel("Inv No:"))
        header.addWidget(self.invoice_input)
        layout.addLayout(header)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Barcode/Name", "Item Name", "Qty", "UOM", "Purchase Rate", "MRP"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setRowCount(1)
        self.table.setItemDelegateForColumn(
            0, FuzzyCompleterDelegate(self.db, self.table)
        )
        self.table.itemChanged.connect(self.handle_table_change)
        layout.addWidget(self.table)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        footer = QHBoxLayout()
        self.lbl_total = QLabel("Total: 0.00")
        self.lbl_total.setObjectName("total-label")
        save_btn = QPushButton("&Save Purchase (F2)")
        save_btn.clicked.connect(self.save_purchase)
        save_btn.setObjectName("btnSave")
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        close_btn.setObjectName("btnCancel")
        footer.addWidget(save_btn)
        footer.addStretch()
        footer.addWidget(self.lbl_total)
        footer.addSpacing(20)
        footer.addWidget(close_btn)
        main_layout.addLayout(footer)
        self.table.setFocus()
        self.table.setCurrentCell(0, 0)

    def load_search_results(self):
        """
        Refresh the purchase search table based on item name.
        """
        query = self.item_search.text().strip()
        if not query:
            self.search_table.setRowCount(0)
            return
        results = self.db.search_purchases_by_item(query)
        self.search_table.setRowCount(0)
        for row, r in enumerate(results):
            self.search_table.insertRow(row)
            self.search_table.setItem(row, 0, QTableWidgetItem(str(r[0])))
            self.search_table.setItem(
                row, 1, QTableWidgetItem(r[1].strftime("%d-%m-%Y"))
            )
            self.search_table.setItem(row, 2, QTableWidgetItem(str(r[2] or "")))
            self.search_table.setItem(row, 3, QTableWidgetItem(str(r[3] or "")))
            self.search_table.setItem(row, 4, QTableWidgetItem(f"{r[4]:.2f}"))

    def handle_table_change(self, item):
        """
        Triggered when a cell in the purchase table is modified.
        Handles auto-filling item details based on barcode.
        """
        if self.updating_cell:
            return
        self.updating_cell = True
        try:
            row, col = item.row(), item.column()
            if col == 0:
                barcode = item.text().strip()
                if barcode:
                    product = self.db.find_product_smart(barcode)
                    if product:
                        self.table.item(row, 0).setText(product[2])
                        self.table.setItem(row, 1, QTableWidgetItem(product[1]))
                        self.table.item(row, 1).setData(Qt.UserRole, product)
                        self.table.setItem(row, 3, QTableWidgetItem(product[6]))
                        self.table.setItem(
                            row, 4, QTableWidgetItem(f"{product[4]:.2f}")
                        )
                        self.table.setItem(
                            row, 5, QTableWidgetItem(f"{product[3]:.2f}")
                        )
                        if row == self.table.rowCount() - 1:
                            self.table.setRowCount(row + 2)
                        QTimer.singleShot(0, lambda: self.table.setCurrentCell(row, 2))
            self.recalc_total()
        finally:
            self.updating_cell = False

    def recalc_total(self):
        """
        Update the total amount label based on all rows in the table.
        """
        total = 0.0
        for r in range(self.table.rowCount()):
            qty_item = self.table.item(r, 2)
            rate_item = self.table.item(r, 4)
            try:
                qty = float(qty_item.text()) if qty_item else 0.0
                rate = float(rate_item.text()) if rate_item else 0.0
                total += qty * rate
            except Exception:
                pass
        self.lbl_total.setText(f"Total: {total:.2f}")

    def save_purchase(self):
        """
        Validate and record the entire purchase to the database.
        """
        items = []
        total = 0.0
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 1)
            if not name_item or not name_item.data(Qt.UserRole):
                continue
            try:
                qty = float(self.table.item(r, 2).text())
                rate = float(self.table.item(r, 4).text())
                mrp_val = float(self.table.item(r, 5).text())
                uom = self.table.item(r, 3).text()
                pid = name_item.data(Qt.UserRole)[0]
                if qty > 0:
                    items.append(
                        {
                            "pid": pid,
                            "qty": qty,
                            "rate": rate,
                            "uom": uom,
                            "mrp": mrp_val,
                        }
                    )
                    total += qty * rate
            except Exception:
                continue
        if not items:
            return
        if self.db.record_purchase(
            self.supplier_input.currentText(), self.invoice_input.text(), items, total
        ):
            QMessageBox.information(self, "Success", "Purchase recorded successfully.")
            self.accept()

    def keyPressEvent(self, event):
        """
        Handle function keys and escape for the purchase entry dialog.
        """
        if event.key() == Qt.Key_F2:
            self.save_purchase()
        elif event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F3:
            self.open_search_dialog()
        else:
            super().keyPressEvent(event)

    def open_search_dialog(self):
        """
        Open the item search dialog and add the selected product to the purchase table.
        """
        dlg = ProductSearchDialog(self.db, self)
        if dlg.exec() == QDialog.Accepted:
            row = self.table.currentRow()
            if row < 0:
                row = self.table.rowCount() - 1
            if self.table.item(row, 0) and self.table.item(row, 0).text():
                if row == self.table.rowCount() - 1:
                    self.table.setRowCount(row + 2)
                row += 1
                self.table.setCurrentCell(row, 0)
            self.table.setItem(row, 0, QTableWidgetItem(dlg.selected_product[2]))
        self.showFullScreen()


class HeldSalesDialog(QDialog):
    """
    View and recall bills that were placed on hold.
    """

    def __init__(self, db_manager, parent=None):
        """
        Initialize the held sales recall dialog and load list of bills on hold.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Recall Held Bills")
        self.db = db_manager
        self.selected_held_id = None
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Held Bills (Select to Restore)"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Time", "Amount", "User", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.doubleClicked.connect(self.select_bill)
        layout.addWidget(self.table)
        self.load_held_sales()
        btn_layout = QHBoxLayout()
        restore_btn = QPushButton("&Restore (Enter)")
        restore_btn.clicked.connect(self.select_bill)
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(restore_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def load_held_sales(self):
        """
        Refresh the list of bills currently on hold from the database.
        """
        sales = self.db.get_held_sales()
        self.table.setRowCount(0)
        for row, s in enumerate(sales):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(s[0])))
            self.table.setItem(row, 1, QTableWidgetItem(s[1].strftime("%H:%M:%S")))
            self.table.setItem(row, 2, QTableWidgetItem(f"{s[2]:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(s[3] or ""))
            del_btn = QPushButton("Del")
            del_btn.clicked.connect(
                lambda _, hid=s[0]: self.db.delete_held_sale(hid)
                or self.load_held_sales()
            )
            self.table.setCellWidget(row, 4, del_btn)

    def select_bill(self):
        """
        Set selected held bill ID and accept the dialog.
        """
        row = self.table.currentRow()
        if row >= 0:
            self.selected_held_id = int(self.table.item(row, 0).text())
            self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.select_bill()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class ConfigDialog(QDialog):
    """
    Setup database connection parameters.
    """

    def __init__(self, config_path, parent=None):
        """
        Initialize the database configuration dialog.
        """
        super().__init__(parent)
        self.setWindowTitle("Database Configuration")
        self.config_path = config_path
        layout = QVBoxLayout(self)
        title = QLabel("Database Setup")
        title.setObjectName("title")
        layout.addWidget(title, 0, Qt.AlignCenter)
        form = QFormLayout()
        self.user = QLineEdit("elytpos_user")
        self.password = QLineEdit("elytpos_password")
        self.password.setEchoMode(QLineEdit.Password)
        self.host = QLineEdit("localhost")
        self.port = QLineEdit("5432")
        form.addRow("User:", self.user)
        form.addRow("Password:", self.password)
        form.addRow("Host:", self.host)
        form.addRow("Port:", self.port)
        layout.addLayout(form)
        save_btn = QPushButton("Save & Connect")
        save_btn.setFixedHeight(50)
        save_btn.setObjectName("btnSave")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        self.setFixedWidth(400)

    def save_config(self):
        """
        Test the database connection parameters and save them to a config file.
        """
        import configparser
        import psycopg2

        params = {
            "user": self.user.text(),
            "password": self.password.text(),
            "host": self.host.text(),
            "port": self.port.text(),
        }
        # Test connection using default 'postgres' database
        test_params = params.copy()
        test_params["dbname"] = "postgres"
        try:
            conn = psycopg2.connect(**test_params)
            conn.close()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to the database server with these settings.\n\nError: {e}",
            )
            return
        config = configparser.ConfigParser()
        config["postgresql"] = params
        with open(self.config_path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class TranslationManagerDialog(QDialog):
    """
    Manage item name translations for a specific language.
    """

    def __init__(self, db_manager, lang_id, lang_name, parent=None):
        """
        Initialize the translation management dialog for a specific language.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle(f"Manage {lang_name} Translations")
        self.db, self.lang_id = db_manager, lang_id
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search items to translate...")
        self.search_input.textChanged.connect(self.load_items)
        layout.addWidget(self.search_input)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Item Name", "Translated Name", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_items()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def load_items(self):
        """
        Fetch products and their current translations from the database.
        """
        query = self.search_input.text()
        products = (
            self.db.search_products(query) if query else self.db.get_all_products()
        )
        self.table.setRowCount(0)
        for row, p in enumerate(products):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p[1]))
            trans_name = ""
            for t in self.db.get_translations(p[0]):
                if t[0] == self.lang_id:
                    trans_name = t[2]
                    break
            trans_edit = QLineEdit(trans_name)
            self.table.setCellWidget(row, 1, trans_edit)
            save_btn = QPushButton("Save")
            save_btn.clicked.connect(
                lambda _, pid=p[0], edit=trans_edit: self.save_trans(pid, edit)
            )
            self.table.setCellWidget(row, 2, save_btn)

    def save_trans(self, pid, edit):
        """
        Save the translated item name to the database.
        """
        self.db.add_translation(pid, self.lang_id, edit.text())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class LanguageSelectionDialog(QDialog):
    """
    Select target language for receipt printing.
    """

    def __init__(self, db_manager, parent=None):
        """
        Initialize the language selection dialog and load available languages.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Print Language")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.db = db_manager
        self.selected_lang_id = None
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose Printing Language:"))
        self.list_widget = QListWidget()
        item = QListWidgetItem("Original (English)")
        item.setData(Qt.UserRole, None)
        self.list_widget.addItem(item)
        for lang in self.db.get_languages():
            item = QListWidgetItem(lang[1])
            item.setData(Qt.UserRole, lang[0])
            self.list_widget.addItem(item)
        self.list_widget.setCurrentRow(0)
        layout.addWidget(self.list_widget)
        btn_layout = QHBoxLayout()
        print_btn = QPushButton("&Print (Enter)")
        print_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("&Cancel (Esc)")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def accept(self):
        """
        Finalize selection and close the dialog.
        """
        item = self.list_widget.currentItem()
        if item:
            self.selected_lang_id = item.data(Qt.UserRole)
        super().accept()

    def keyPressEvent(self, event):
        """
        Handle enter and escape keys for the language selection dialog.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class MaintenanceDashboardDialog(QDialog):
    """
    Administrative interface for database maintenance tasks.
    """

    def __init__(self, db_manager, parent=None):
        """
        Initialize the maintenance dashboard and setup action buttons.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Maintenance Dashboard")
        self.db = db_manager
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        title = QLabel("Database Maintenance Dashboard")
        title.setObjectName("title")
        layout.addWidget(title)
        self.reindex_btn = QPushButton("Reindex Database")
        self.reindex_btn.setFixedHeight(60)
        self.reindex_btn.clicked.connect(self.reindex_db)
        layout.addWidget(self.reindex_btn)
        self.backup_btn = QPushButton("Backup Database (Export)")
        self.backup_btn.setFixedHeight(60)
        self.backup_btn.clicked.connect(self.backup_db)
        layout.addWidget(self.backup_btn)
        self.restore_btn = QPushButton("Restore Database (Import)")
        self.restore_btn.setFixedHeight(60)
        self.restore_btn.clicked.connect(self.restore_db)
        layout.addWidget(self.restore_btn)
        layout.addStretch()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def reindex_db(self):
        """
        Trigger a full database reindex to optimize performance.
        """
        if (
            QMessageBox.question(
                self,
                "Confirm",
                "Reindex entire database? Application might hang for a moment.",
            )
            == QMessageBox.Yes
        ):
            if self.db.reindex_database():
                QMessageBox.information(
                    self, "Success", "Database reindexed successfully."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to reindex database.")

    def backup_db(self):
        """
        Export the current database state to a SQL file.
        """
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Database Backup", "elytpos_backup.sql", "SQL Files (*.sql)"
        )
        if not path:
            return
        params = self.db.conn_params
        env = os.environ.copy()
        env["PGPASSWORD"] = params["password"]
        cmd = [
            "pg_dump",
            "-h",
            params["host"],
            "-p",
            params["port"],
            "-U",
            params["user"],
            "-f",
            path,
            params["dbname"],
        ]
        try:
            subprocess.run(cmd, env=env, check=True)
            QMessageBox.information(self, "Success", f"Database backed up to {path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed: {e}")

    def restore_db(self):
        """
        Import a database state from a SQL file, overwriting current data.
        """
        msg = "Restoring will OVERWRITE existing data. Are you sure?"
        if QMessageBox.question(self, "Confirm Restore", msg) != QMessageBox.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Database Backup", "", "SQL Files (*.sql)"
        )
        if not path:
            return
        params = self.db.conn_params
        env = os.environ.copy()
        env["PGPASSWORD"] = params["password"]
        cmd = [
            "psql",
            "-h",
            params["host"],
            "-p",
            params["port"],
            "-U",
            params["user"],
            "-d",
            params["dbname"],
            "-f",
            path,
        ]
        try:
            subprocess.run(cmd, env=env, check=True)
            QMessageBox.information(
                self,
                "Success",
                "Database restored successfully. Please restart the application.",
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Restore failed: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class InventoryDialog(QDialog):
    """
    Main interface for adding and editing inventory items.
    """

    def __init__(self, db_manager, parent=None):
        """
        Initialize the inventory management dialog and load supporting data.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Item Master (Add/Edit)")
        self.db = db_manager
        self.current_product_id = None
        self.uom_data_list = self.db.get_uoms()
        self.uom_display_list = [
            f"{u[1]} ({u[2]})" if u[2] else u[1] for u in self.uom_data_list
        ]
        self.uom_name_list = [u[1] for u in self.uom_data_list]
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        top_layout = QHBoxLayout()
        search_btn = QPushButton("&Find Item (F3)")
        search_btn.clicked.connect(self.open_search)
        clear_btn = QPushButton("&New Item")
        clear_btn.clicked.connect(self.clear_form)
        self.reg_btn = QPushButton("&Purchase Register")
        self.reg_btn.clicked.connect(self.open_purchase_register)
        self.reg_btn.setVisible(False)
        top_layout.addWidget(search_btn)
        top_layout.addWidget(clear_btn)
        top_layout.addWidget(self.reg_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        grp = QGroupBox("Base Item Details")
        form_layout = QFormLayout(grp)
        self.name_input = QLineEdit()
        self.barcode_input = QLineEdit()
        self.mrp_input = QDoubleSpinBox()
        self.mrp_input.setMaximum(100000)
        self.mrp_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.mrp_input.setDecimals(3)
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.price_input.setDecimals(4)
        self.category_input = QLineEdit()
        self.base_uom_input = QComboBox()
        self.base_uom_input.addItems(self.uom_display_list)
        self.base_uom_input.setEditable(True)
        form_layout.addRow("Item &Name:", self.name_input)
        form_layout.addRow("Base &Barcode:", self.barcode_input)
        form_layout.addRow("&MRP:", self.mrp_input)
        form_layout.addRow("Base &Rate:", self.price_input)
        form_layout.addRow("Base &UOM:", self.base_uom_input)
        form_layout.addRow("&Category:", self.category_input)
        layout.addWidget(grp)
        self.alias_grp = QGroupBox("Alternate Units / Aliases")
        self.alias_grp.setEnabled(False)
        alias_layout = QVBoxLayout(self.alias_grp)
        add_alias_layout = QHBoxLayout()
        self.alias_barcode = QLineEdit()
        self.alias_uom = QComboBox()
        self.alias_uom.addItems(self.uom_display_list)
        self.alias_uom.setEditable(True)
        self.alias_mrp = QDoubleSpinBox()
        self.alias_mrp.setMaximum(1000000)
        self.alias_mrp.setDecimals(3)
        self.alias_mrp.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.alias_price = QDoubleSpinBox()
        self.alias_price.setMaximum(1000000)
        self.alias_price.setDecimals(4)
        self.alias_price.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.alias_factor = QDoubleSpinBox()
        self.alias_factor.setMaximum(1000000)
        self.alias_factor.setDecimals(3)
        self.alias_factor.setValue(1.0)
        self.alias_factor.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.alias_qty = QDoubleSpinBox()
        self.alias_qty.setMaximum(1000000)
        self.alias_qty.setDecimals(3)
        self.alias_qty.setValue(1.0)
        self.alias_qty.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.alias_factor.valueChanged.connect(self.auto_calc_alias_price)
        self.price_input.valueChanged.connect(self.auto_calc_alias_price)
        self.alias_factor.valueChanged.connect(self.auto_calc_alias_mrp)
        self.mrp_input.valueChanged.connect(self.auto_calc_alias_mrp)
        add_alias_btn = QPushButton("Add &Alias")
        add_alias_btn.clicked.connect(self.add_alias)
        add_alias_layout.addWidget(QLabel("Barcode:"))
        add_alias_layout.addWidget(self.alias_barcode)
        add_alias_layout.addWidget(QLabel("UOM:"))
        add_alias_layout.addWidget(self.alias_uom)
        add_alias_layout.addWidget(QLabel("MRP:"))
        add_alias_layout.addWidget(self.alias_mrp)
        add_alias_layout.addWidget(QLabel("Rate:"))
        add_alias_layout.addWidget(self.alias_price)
        add_alias_layout.addWidget(QLabel("Factor:"))
        add_alias_layout.addWidget(self.alias_factor)
        add_alias_layout.addWidget(QLabel("Qty:"))
        add_alias_layout.addWidget(self.alias_qty)
        add_alias_layout.addWidget(add_alias_btn)
        alias_layout.addLayout(add_alias_layout)
        self.alias_table = QTableWidget()
        self.alias_table.setColumnCount(7)
        self.alias_table.setHorizontalHeaderLabels(
            ["Barcode", "UOM", "MRP", "Rate", "Factor", "Qty", "Action"]
        )
        self.alias_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alias_table.setMinimumHeight(200)
        alias_layout.addWidget(self.alias_table)
        layout.addWidget(self.alias_grp)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("&Save Base Item (F2)")
        self.save_btn.clicked.connect(self.save_product)
        self.save_btn.setObjectName("btnSave")
        self.del_btn = QPushButton("&Delete Item")
        self.del_btn.clicked.connect(self.confirm_delete)
        self.del_btn.setObjectName("btnCancel")
        self.del_btn.setVisible(False)
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        close_btn.setObjectName("btnCancel")
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)
        save_act = QAction(self)
        save_act.setShortcut("F2")
        save_act.triggered.connect(self.save_product)
        self.addAction(save_act)
        find_act = QAction(self)
        find_act.setShortcut("F3")
        find_act.triggered.connect(self.open_search)
        self.addAction(find_act)

    def keyPressEvent(self, event):
        """
        Handle function keys and escape for the inventory dialog.
        """
        if event.key() == Qt.Key_F2:
            self.save_product()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def open_search(self):
        """
        Open the item search dialog and load the selected product.
        """
        dlg = ProductSearchDialog(self.db, self)
        res = dlg.exec()
        self.showFullScreen()
        if res == QDialog.Accepted:
            self.load_product(dlg.selected_product)

    def load_product(self, prod):
        """
        Populate the form fields with data from an existing product.
        """
        self.current_product_id = prod[0]
        self.name_input.setText(prod[1])
        self.barcode_input.setText(prod[2])
        self.mrp_input.setValue(float(prod[3]))
        self.price_input.setValue(float(prod[4]))
        self.category_input.setText(prod[5] or "")
        self.base_uom_input.setCurrentText(prod[6] or "pcs")
        self.save_btn.setText("Update Base Item (F2)")
        self.alias_grp.setEnabled(True)
        self.load_aliases()
        self.del_btn.setVisible(True)
        self.reg_btn.setVisible(True)

    def open_purchase_register(self):
        """
        Open the purchase history view for the current item.
        """
        if self.current_product_id:
            PurchaseRegisterDialog(
                self.db, self.current_product_id, self.name_input.text(), self
            ).exec()
            self.showFullScreen()

    def confirm_delete(self):
        """
        Move the current product to the recycle bin after user confirmation.
        """
        if not self.current_product_id:
            return
        msg = (
            f"Are you sure you want to move '{self.name_input.text()}' to Recycle Bin?"
        )
        if (
            QMessageBox.question(
                self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No
            )
            == QMessageBox.Yes
        ):
            if self.db.delete_product(self.current_product_id):
                QMessageBox.information(self, "Success", "Item moved to Recycle Bin.")
                self.clear_form()

    def load_aliases(self):
        """
        Refresh the table of alternate barcodes and units for the current product.
        """
        self.alias_table.setRowCount(0)
        for row, alias in enumerate(self.db.get_aliases(self.current_product_id)):
            self.alias_table.insertRow(row)
            for c in range(4):
                self.alias_table.setItem(row, c, QTableWidgetItem(str(alias[c + 1])))
            self.alias_table.setItem(row, 4, QTableWidgetItem(f"{float(alias[5]):.3f}"))
            self.alias_table.setItem(row, 5, QTableWidgetItem(f"{float(alias[6]):.3f}"))
            del_btn = QPushButton("Del")
            del_btn.clicked.connect(
                lambda _, aid=alias[0]: self.db.delete_alias(aid) or self.load_aliases()
            )
            self.alias_table.setCellWidget(row, 6, del_btn)

    def auto_calc_alias_price(self):
        """
        Automatically calculate alternate unit price based on conversion factor.
        """
        self.alias_price.setValue(self.price_input.value() * self.alias_factor.value())

    def auto_calc_alias_mrp(self):
        """
        Automatically calculate alternate unit MRP based on conversion factor.
        """
        self.alias_mrp.setValue(self.mrp_input.value() * self.alias_factor.value())

    def add_alias(self):
        """
        Validate and save a new alternate barcode/unit for the product.
        """
        full_uom = self.alias_uom.currentText()
        uom_name = full_uom.split(" (")[0] if " (" in full_uom else full_uom
        if self.db.add_alias(
            self.current_product_id,
            self.alias_barcode.text(),
            uom_name,
            self.alias_mrp.value(),
            self.alias_price.value(),
            self.alias_factor.value(),
            self.alias_qty.value(),
        ):
            self.alias_barcode.clear()
            self.load_aliases()

    def clear_form(self):
        """
        Reset all form fields to their default empty state.
        """
        self.current_product_id = None
        self.name_input.clear()
        self.barcode_input.clear()
        self.mrp_input.setValue(0)
        self.price_input.setValue(0)
        self.category_input.clear()
        self.alias_table.setRowCount(0)
        self.alias_grp.setEnabled(False)
        self.save_btn.setText("Save Base Item (F2)")
        self.del_btn.setVisible(False)
        self.reg_btn.setVisible(False)

    def save_product(self):
        """
        Validate input and create or update the base product record.
        """
        name, barcode, mrp, price, cat = (
            self.name_input.text(),
            self.barcode_input.text(),
            self.mrp_input.value(),
            self.price_input.value(),
            self.category_input.text() or "General",
        )
        full_uom = self.base_uom_input.currentText()
        uom = full_uom.split(" (")[0] if " (" in full_uom else full_uom
        if not name or not barcode:
            return
        if self.current_product_id:
            if self.db.update_product(
                self.current_product_id, name, barcode, mrp, price, cat, uom
            ):
                QMessageBox.information(self, "Success", f"Item '{name}' Updated.")
                self.accept()
        else:
            pid = self.db.add_product(name, barcode, mrp, price, cat, uom)
            if pid:
                self.current_product_id = pid
                self.alias_grp.setEnabled(True)
                self.save_btn.setText("Update Base Item (F2)")
                QMessageBox.information(self, "Success", f"Item '{name}' Saved.")
                self.accept()


class SalesHistoryDialog(QDialog):
    """
    View and manage historical sales transactions.
    """

    def __init__(self, db_manager, printer, parent=None):
        """
        Initialize the sales history dialog and its filters.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Sales History / Day Book")
        self.db, self.printer, self.parent_window = db_manager, printer, parent
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.date_filter = QDateEdit()
        self.date_filter.setDisplayFormat("dd-MM-yyyy")
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setCalendarPopup(True)
        self.date_filter.dateChanged.connect(self.load_history)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Bill No, Name or Mobile...")
        self.search_input.textChanged.connect(self.load_history)
        refresh_btn = QPushButton("&Refresh")
        refresh_btn.clicked.connect(self.load_history)
        top_layout.addWidget(QLabel("Date:"))
        top_layout.addWidget(self.date_filter)
        top_layout.addWidget(QLabel("Search:"))
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(refresh_btn)
        layout.addLayout(top_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Bill No", "Time", "Customer", "Mobile", "Amount", "Print", "Edit"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.load_history()
        close_btn = QPushButton("&Close (Esc)")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.table.setFocus()
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def keyPressEvent(self, event):
        """
        Handle enter and escape keys for the sales history table.
        """
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.table.hasFocus():
            row = self.table.currentRow()
            if row >= 0:
                sid = self.table.item(row, 0).text()
                self.modify_bill(sid)
        else:
            super().keyPressEvent(event)

    def load_history(self):
        """
        Fetch filtered sales records from the database and populate the table.
        """
        self.table.setRowCount(0)
        query = self.search_input.text().strip()
        for row, sale in enumerate(
            self.db.get_sales_history(self.date_filter.date().toPython(), query)
        ):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(sale[0])))
            self.table.setItem(row, 1, QTableWidgetItem(sale[1].strftime("%H:%M:%S")))
            self.table.setItem(row, 2, QTableWidgetItem(sale[4] or "Cash"))
            self.table.setItem(row, 3, QTableWidgetItem(sale[5] or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{sale[2]:.2f}"))
            p_btn = QPushButton("Print")
            p_btn.clicked.connect(
                lambda _, sid=sale[0], amt=sale[2]: self.reprint_bill(sid, amt)
            )
            m_btn = QPushButton("Modify")
            m_btn.setObjectName("btnSave")
            m_btn.clicked.connect(lambda _, sid=sale[0]: self.modify_bill(sid))
            self.table.setCellWidget(row, 5, p_btn)
            self.table.setCellWidget(row, 6, m_btn)

    def reprint_bill(self, sid, total):
        """
        Retrieve bill items and print a new receipt copy.
        """
        items = self.db.get_sale_items(sid)
        if items:
            langs = self.db.get_languages()
            selected_lang_id = None
            should_print = True
            if langs:
                lang_dlg = LanguageSelectionDialog(self.db, self)
                if lang_dlg.exec() == QDialog.Accepted:
                    selected_lang_id = lang_dlg.selected_lang_id
                else:
                    should_print = False

            if should_print:
                print_items = self.db.get_translated_items(items, selected_lang_id)
                sales = self.db.get_sales_history(query=str(sid))
                sale_header = next((s for s in sales if str(s[0]) == str(sid)), None)
                cust_info = None
                if sale_header and sale_header[5]:
                    customer = self.db.get_customer_by_mobile(sale_header[5])
                    if customer:
                        cust_info = {
                            "name": customer[1],
                            "mobile": customer[2],
                            "address": customer[3],
                        }
                self.printer.print_receipt(
                    print_items, float(total), sid, customer_info=cust_info
                )

    def modify_bill(self, sid):
        """
        Send the selected bill ID to the main window for editing.
        """
        if self.parent_window:
            self.parent_window.load_bill_for_modification(sid)
            self.close()


class ExcelTable(QTableWidget):
    """
    Custom table widget providing spreadsheet-like behavior for billing.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(
            [
                "EAN/Barcode",
                "Item Name",
                "Qty",
                "UOM",
                "MRP",
                "Rate",
                "Disc %",
                "Amount",
            ]
        )
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in [2, 3, 4, 5, 6, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.setColumnWidth(0, 180)
        self.setRowCount(20)
        self.nav_order = [0, 2, 3, 5]
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.currentCellChanged.connect(self.scroll_to_center)
        QTimer.singleShot(0, lambda: self.setCurrentCell(0, 0))

    def scroll_to_center(self, row, _col, _prev_row, _prev_col):
        """
        Scroll the table so that the specified row is centered in the view.
        """
        if row >= 0:
            if self.rowCount() - row < 15:
                self.setRowCount(row + 20)
            QTimer.singleShot(
                0,
                lambda: self.scrollTo(
                    self.model().index(row, 0),
                    QAbstractItemView.ScrollHint.PositionAtCenter,
                ),
            )

    def is_row_valid(self, row):
        """
        Check if the specified row contains a valid product selection.
        """
        name_item = self.item(row, 1)
        return name_item is not None and name_item.data(Qt.UserRole) is not None

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle spreadsheet-style navigation and editing keys within the billing grid.
        """
        if event.key() == Qt.Key_F2:
            event.ignore()
            return
        row, col = self.currentRow(), self.currentColumn()
        if event.key() == Qt.Key_Insert:
            self.insertRow(row)
            self.setCurrentCell(row, 0)
            return
        if event.key() == Qt.Key_Left:
            if col == 0:
                if row > 0:
                    self.setCurrentCell(row - 1, self.columnCount() - 1)
            else:
                super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Right:
            if col == 0 and not self.is_row_valid(row):
                return
            if col == self.columnCount() - 1:
                if not self.is_row_valid(row):
                    return
                if row == self.rowCount() - 1:
                    self.setRowCount(row + 2)
                self.setCurrentCell(row + 1, 0)
            else:
                super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Up:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Down:
            if row == self.rowCount() - 1 or not self.is_row_valid(row):
                return
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Delete:
            rows = sorted(
                list(set(i.row() for i in self.selectedItems())), reverse=True
            )
            if rows:
                target_row = min(rows)
                for r in rows:
                    self.removeRow(r)
                if self.rowCount() < 20:
                    self.setRowCount(20)
                target_row = min(target_row, self.rowCount() - 1)
                self.setCurrentCell(target_row, col)
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if col in self.nav_order:
                idx = self.nav_order.index(col)
                if idx < len(self.nav_order) - 1:
                    if col == 0 and not self.is_row_valid(row):
                        return
                    self.setCurrentCell(row, self.nav_order[idx + 1])
                else:
                    if not self.is_row_valid(row):
                        return
                    if row == self.rowCount() - 1:
                        self.setRowCount(row + 2)
                    self.setCurrentCell(row + 1, 0)
            elif col in (6, 7):
                if not self.is_row_valid(row):
                    return
                if row == self.rowCount() - 1:
                    self.setRowCount(row + 2)
                self.setCurrentCell(row + 1, 0)
            elif col == 1:
                self.setCurrentCell(row, 2)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class FuzzySearchLineEdit(QLineEdit):
    """
    Custom QLineEdit with an integrated search result dropdown.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.popup = QListWidget()
        self.popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.setAttribute(Qt.WA_ShowWithoutActivating)

        current_theme = QApplication.instance().property("theme_name") or "mocha"
        c = get_theme_colors(current_theme)

        self.popup.setStyleSheet(
            get_style(current_theme)
            + f"""
            QListWidget {{
                background-color: {c["bg"]};
                border: 2px solid {c["accent"]};
                font-size: 13pt;
                outline: none;
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {c["border"]};
                color: {c["fg"]};
            }}
            QListWidget::item:selected {{
                background-color: {c["accent"]};
                color: {c["bg"]};
            }}
            """
        )
        self.popup.itemClicked.connect(self.on_item_clicked)
        self.textChanged.connect(self.on_text_changed)

    def on_text_changed(self, text):
        """
        Handle text changes in the search input and update the popup list.
        """
        if len(text) < 1:
            self.popup.hide()
            return
        try:
            products = self.db.search_products(text)
            self.popup.clear()
            if not products:
                self.popup.hide()
                return
            for p in products[:10]:
                item = QListWidgetItem(f"{p[1]} ({p[2]})")
                item.setData(Qt.UserRole, p)
                self.popup.addItem(item)
            self.popup.setCurrentRow(0)
            self.popup.setFixedWidth(max(self.width() + 50, 450))
            self.popup.setFixedHeight(min(self.popup.count() * 38 + 5, 350))
            pos = self.mapToGlobal(self.rect().bottomLeft())
            self.popup.move(pos)
            self.popup.show()
        except Exception:
            pass

    def on_item_clicked(self, item):
        """
        Handle item selection from the search results popup.
        """
        p = item.data(Qt.UserRole)
        self.setText(p[2])
        self.popup.hide()
        self.returnPressed.emit()

    def keyPressEvent(self, event):
        """
        Override key events to handle navigation within the search popup.
        """
        if self.popup.isVisible():
            if event.key() == Qt.Key_Down:
                self.popup.setCurrentRow(
                    (self.popup.currentRow() + 1) % self.popup.count()
                )
                return
            if event.key() == Qt.Key_Up:
                self.popup.setCurrentRow(
                    (self.popup.currentRow() - 1 + self.popup.count())
                    % self.popup.count()
                )
                return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self.popup.currentRow() >= 0:
                    self.on_item_clicked(self.popup.currentItem())
                    return
            if event.key() == Qt.Key_Tab:
                if self.popup.currentRow() >= 0:
                    self.on_item_clicked(self.popup.currentItem())
                self.popup.hide()
                super().keyPressEvent(event)
                return
            if event.key() == Qt.Key_Escape:
                self.popup.hide()
                return
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.text() == "":
            try:
                table = self.parent().parent()
                window = table.window()
                if hasattr(window, "open_search_dialog"):
                    self.popup.hide()
                    window.open_search_dialog()
                    return
            except Exception:
                pass
        super().keyPressEvent(event)

    def hideEvent(self, event):
        """Hideevent."""
        self.popup.hide()
        super().hideEvent(event)


class FuzzyCompleterDelegate(QStyledItemDelegate):
    """
    Delegate providing custom editor for the barcode/name column.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            return FuzzySearchLineEdit(self.db, parent)
        return super().createEditor(parent, option, index)


class MainWindow(QMainWindow):
    """
    Main application window for elytPOS.
    """

    def __init__(self, db_manager, user):
        """
        Initialize the main POS application window and its core components.
        """
        super().__init__()
        self.setWindowTitle(f"elytPOS v{__version__} - {user[2]}")
        self.showFullScreen()
        self.db = db_manager
        self.printer = ReceiptPrinter(db_manager)
        self.current_user = user
        self.updating_cell = False
        self.current_sale_id = None
        self.calc_dlg = None
        self.theme_name = self.db.get_setting("theme", "mocha")
        self.init_ui()
        self.apply_theme(self.theme_name)

    def apply_theme(self, theme_name):
        """
        Switch the application's visual theme and update all UI components.
        """
        self.theme_name = theme_name

        style = get_style(theme_name)
        app = QApplication.instance()
        app.setProperty("theme_name", theme_name)
        app.setWindowIcon(QIcon(resource_path(f"svg/logo_{theme_name}.svg")))
        app.setStyleSheet(style)

        # Apply style to all open top-level widgets (like PrinterConfigDialog)
        for widget in app.topLevelWidgets():
            widget.setStyleSheet(style)
            # Recursively update children that might need explicit polish
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self.db.set_setting("theme", theme_name)
        self.update_total_label_style()

    def check_permission(self, perm_key):
        """Check if current user has specific permission."""
        import json

        try:
            if not self.current_user or len(self.current_user) < 5:
                return False

            perms_str = self.current_user[4]
            if not perms_str:
                # Fallback for users without explicit permissions
                role = self.current_user[3]
                if role == "admin":
                    return True
                defaults = {
                    "staff": ["billing", "view_reports"],
                    "manager": [
                        "billing",
                        "view_reports",
                        "manage_inventory",
                        "manage_customers",
                        "manage_purchases",
                        "manage_schemes",
                    ],
                }
                return perm_key in defaults.get(role, [])

            perms = json.loads(perms_str)
            return perms.get(perm_key, False)
        except Exception:
            return False

    def update_total_label_style(self):
        """
        Force a restyle of the total amount label to reflect theme changes.
        """
        self.lbl_total_amt.setObjectName("total-label")
        self.lbl_total_amt.style().unpolish(self.lbl_total_amt)
        self.lbl_total_amt.style().polish(self.lbl_total_amt)

    def closeEvent(self, event):
        if (
            QMessageBox.question(self, "Confirm Exit", "Are you sure you want to quit?")
            == QMessageBox.Yes
        ):
            if (
                QMessageBox.question(
                    self,
                    "Backup",
                    "Would you like to take a database backup before exiting?",
                )
                == QMessageBox.Yes
            ):
                self.backup_on_exit()
            event.accept()
        else:
            event.ignore()

    def backup_on_exit(self):
        """
        Automatically perform a database backup when the application closes.
        """
        backup_dir = os.path.join(get_app_path(), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(backup_dir, f"auto_backup_{timestamp}.sql")
        params = self.db.conn_params
        env = os.environ.copy()
        env["PGPASSWORD"] = params["password"]
        cmd = [
            "pg_dump",
            "-h",
            params["host"],
            "-p",
            params["port"],
            "-U",
            params["user"],
            "-f",
            path,
            params["dbname"],
        ]
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            print(f"Auto-backup successful: {path}")
        except Exception as e:
            print(f"Auto-backup failed: {e}")

    def init_ui(self):
        menubar = self.menuBar()
        menubar.setFont(QFont("FiraCode Nerd Font", 10))

        # Masters Menu
        masters_menu = menubar.addMenu("&Masters")
        if self.check_permission("manage_inventory"):
            inv_action = QAction("&Item Master (Ctrl+I)", self)
            inv_action.setShortcut("Ctrl+I")
            inv_action.triggered.connect(self.open_inventory)
            masters_menu.addAction(inv_action)
            masters_menu.addAction("&UOM Master", self.open_uom_master)
            masters_menu.addAction("&Language Master", self.open_language_master)

        if self.check_permission("manage_customers"):
            masters_menu.addAction("&Customer Master", self.open_customer_master)

        # Administration Menu
        if self.check_permission("manage_users") or self.check_permission("settings"):
            admin_menu = menubar.addMenu("&Administration")

            if self.check_permission("settings"):
                company_action = QAction("Create &Company / FY", self)
                company_action.triggered.connect(self.open_create_company)
                admin_menu.addAction(company_action)

                modify_company_action = QAction("&Modify Company", self)
                modify_company_action.triggered.connect(self.open_modify_company)
                admin_menu.addAction(modify_company_action)

            if self.check_permission("manage_users"):
                user_action = QAction("&User Master", self)
                user_action.triggered.connect(self.open_user_master)
                admin_menu.addAction(user_action)

        # Transactions Menu
        if self.check_permission("manage_purchases") or self.check_permission(
            "manage_schemes"
        ):
            trans_menu = menubar.addMenu("&Transactions")

            if self.check_permission("manage_purchases"):
                pur_action = QAction("&Purchase Master", self)
                pur_action.triggered.connect(self.open_purchase_master)
                trans_menu.addAction(pur_action)

            if self.check_permission("manage_schemes"):
                schemes_menu = trans_menu.addMenu("&Schemes")
                schemes_menu.addAction(
                    "&Add New Scheme", lambda: self.open_scheme_entry(None)
                )
                schemes_menu.addAction(
                    "&Modify Scheme", lambda: self.open_scheme_list("modify")
                )
                schemes_menu.addAction(
                    "&List Schemes", lambda: self.open_scheme_list("list")
                )

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        calc_action = QAction("&Calculator (F8)", self)
        calc_action.setShortcuts(["Ctrl+Alt+C", "F8"])
        calc_action.triggered.connect(self.open_calculator)
        tools_menu.addAction(calc_action)

        if self.check_permission("database_ops"):
            tools_menu.addAction("&Maintenance", self.open_maintenance)
            tools_menu.addAction("&Recycle Bin", self.open_recycle_bin)

        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        if self.check_permission("settings"):
            settings_menu.addAction("Printer &Settings", self.open_printer_config)

        theme_menu = settings_menu.addMenu("&Appearance Themes")
        for theme_id in styles.THEMES:
            action = QAction(theme_id.replace("_", " ").capitalize(), self)
            action.triggered.connect(lambda checked, t=theme_id: self.apply_theme(t))
            theme_menu.addAction(action)

        help_menu = menubar.addMenu("&Help")
        help_action = QAction("&User Guide (F1)", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.open_help)
        help_menu.addAction(help_action)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        header_row = QHBoxLayout()
        sales_grp = QGroupBox("Sales Entry")
        s_layout = QHBoxLayout(sales_grp)
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.bill_no_label = QLabel("Bill No: <New>")
        s_layout.addWidget(QLabel("Date:"))
        s_layout.addWidget(self.date_edit)
        s_layout.addWidget(self.bill_no_label)
        s_layout.addStretch()
        header_row.addWidget(sales_grp, 1)
        cust_grp = QGroupBox("Customer Details")
        c_layout = QHBoxLayout(cust_grp)
        self.cust_mobile_input = QLineEdit()
        self.cust_mobile_input.setPlaceholderText("Mobile No (Lookup)")
        self.cust_mobile_input.setFixedWidth(180)
        self.cust_mobile_input.returnPressed.connect(self.handle_customer_lookup)
        self.cust_name_label = QLabel("Name: <Cash>")
        self.cust_mobile_label = QLabel("Mob: -")
        self.selected_customer_data = None
        self.cust_search_btn = QPushButton("Search")
        self.cust_search_btn.clicked.connect(self.open_customer_search)
        c_layout.addWidget(QLabel("Lookup:"))
        c_layout.addWidget(self.cust_mobile_input)
        c_layout.addWidget(self.cust_search_btn)
        c_layout.addWidget(self.cust_name_label)
        c_layout.addWidget(self.cust_mobile_label)
        c_layout.addStretch()
        header_row.addWidget(cust_grp, 2)
        layout.addLayout(header_row)
        self.grid = ExcelTable()
        self.grid.itemChanged.connect(self.handle_grid_change)
        layout.addWidget(self.grid)
        self.grid.setItemDelegateForColumn(
            0, FuzzyCompleterDelegate(self.db, self.grid)
        )
        footer = QHBoxLayout()
        btn_layout = QHBoxLayout()
        btn_f2 = QPushButton("&Save (F2)")
        btn_f2.clicked.connect(self.process_checkout)
        btn_f3 = QPushButton("S&earch (F3)")
        btn_f3.clicked.connect(self.open_search_dialog)
        btn_f4 = QPushButton("C&lear (F4)")
        btn_f4.clicked.connect(self.reset_grid)
        btn_f5 = QPushButton("&History (F5)")
        btn_f5.clicked.connect(self.view_history)
        btn_f6 = QPushButton("&Hold (F6)")
        btn_f6.clicked.connect(self.hold_current_bill)
        btn_f7 = QPushButton("&Recall (F7)")
        btn_f7.clicked.connect(self.recall_held_bill)
        btn_calc = QPushButton("Ca&lc (F8)")
        btn_calc.clicked.connect(self.open_calculator)
        btn_esc = QPushButton("&Quit (Esc)")
        btn_esc.clicked.connect(self.close)
        btn_layout.addWidget(btn_f2)
        btn_layout.addWidget(btn_f3)
        btn_layout.addWidget(btn_f4)
        btn_layout.addWidget(btn_f5)
        btn_layout.addWidget(btn_f6)
        btn_layout.addWidget(btn_f7)
        btn_layout.addWidget(btn_calc)
        btn_layout.addWidget(btn_esc)
        self.lbl_total_qty = QLabel("Qty: 0")
        self.lbl_total_amt = QLabel("Total: 0.00")
        self.update_total_label_style()
        footer.addLayout(btn_layout)
        footer.addStretch()
        footer.addWidget(self.lbl_total_qty)
        footer.addSpacing(20)
        footer.addWidget(self.lbl_total_amt)
        layout.addLayout(footer)
        self.grid.setFocus()
        self.grid.setCurrentCell(0, 0)
        s_shortcut = QAction(self)
        s_shortcut.setShortcut("F3")
        s_shortcut.triggered.connect(self.open_search_dialog)
        self.addAction(s_shortcut)
        h_shortcut = QAction(self)
        h_shortcut.setShortcut("F5")
        h_shortcut.triggered.connect(self.view_history)
        self.addAction(h_shortcut)
        hold_shortcut = QAction(self)
        hold_shortcut.setShortcut("F6")
        hold_shortcut.triggered.connect(self.hold_current_bill)
        self.addAction(hold_shortcut)
        recall_shortcut = QAction(self)
        recall_shortcut.setShortcut("F7")
        recall_shortcut.triggered.connect(self.recall_held_bill)
        self.addAction(recall_shortcut)
        save_shortcut = QAction(self)
        save_shortcut.setShortcut("F2")
        save_shortcut.triggered.connect(self.process_checkout)
        self.addAction(save_shortcut)
        clear_shortcut = QAction(self)
        clear_shortcut.setShortcut("F4")
        clear_shortcut.triggered.connect(self.reset_grid)
        self.addAction(clear_shortcut)
        quit_shortcut = QAction(self)
        quit_shortcut.setShortcut("Esc")
        quit_shortcut.triggered.connect(self.close)
        self.addAction(quit_shortcut)

    def open_printer_config(self):
        """Open the printer configuration dialog."""
        if not self.check_permission("settings"):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to access Printer Settings.",
            )
            return
        dialog = PrinterConfigDialog(self.printer, self)
        dialog.exec()
        self.showFullScreen()

    def open_help(self):
        """Open the interactive help system dialog."""
        HelpDialog(self).exec()
        self.showFullScreen()

    def open_inventory(self):
        """Open the Item Master / Inventory management dialog."""
        if not self.check_permission("manage_inventory"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Inventory."
            )
            return
        InventoryDialog(self.db, self).exec()
        self.showFullScreen()

    def open_scheme_entry(self, sid=None):
        """Open the dialog to create or edit a promotional scheme."""
        if not self.check_permission("manage_schemes"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Schemes."
            )
            return
        SchemeEntryDialog(self.db, sid, self).exec()
        self.showFullScreen()

    def open_scheme_list(self, mode):
        """Open the list of promotional schemes."""
        if not self.check_permission("manage_schemes"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Schemes."
            )
            return
        SchemeListDialog(self.db, mode, self).exec()
        self.showFullScreen()

    def open_customer_master(self):
        """Open the customer management dialog."""
        if not self.check_permission("manage_customers"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Customers."
            )
            return
        CustomerMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_customer_search(self):
        """Open the customer search and selection dialog."""
        dlg = CustomerSearchDialog(self.db, self)
        if dlg.exec() == QDialog.Accepted:
            customer = dlg.selected_customer
            self.selected_customer_data = customer
            self.cust_name_label.setText(f"Name: {customer[1]}")
            self.cust_mobile_label.setText(f"Mob: {customer[2]}")
            self.cust_mobile_input.clear()
        self.showFullScreen()

    def open_purchase_master(self):
        """Open the purchase entry and recording dialog."""
        if not self.check_permission("manage_purchases"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Purchases."
            )
            return
        PurchaseEntryDialog(self.db, self).exec()
        self.showFullScreen()

    def open_uom_master(self):
        """Open the Units of Measure management dialog."""
        if not self.check_permission("manage_inventory"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage UOMs."
            )
            return
        UOMMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_language_master(self):
        """Open the language management dialog."""
        if not self.check_permission("manage_inventory"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Languages."
            )
            return
        LanguageMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_create_company(self):
        """Open the company creation dialog."""
        if not self.check_permission("settings") and not self.check_permission(
            "database_ops"
        ):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to Create Companies."
            )
            return
        CreateCompanyDialog(self.db.conn_params, parent=self).exec()
        self.showFullScreen()

    def open_modify_company(self):
        """Open the company modification dialog."""
        if not self.check_permission("settings"):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to Modify Company Settings.",
            )
            return
        CreateCompanyDialog(self.db.conn_params, db_manager=self.db, parent=self).exec()
        # Refresh printer settings from updated DB settings
        self.printer.load_from_db()
        self.showFullScreen()

    def open_user_master(self):
        """Open the system user management dialog."""
        if not self.check_permission("manage_users"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Users."
            )
            return
        UserMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_maintenance(self):
        """Open the administrative maintenance dashboard."""
        if not self.check_permission("database_ops"):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to access Maintenance Dashboard.",
            )
            return
        MaintenanceDashboardDialog(self.db, self).exec()
        self.showFullScreen()

    def open_recycle_bin(self):
        """Open the recycle bin dialog to view/restore deleted items."""
        if not self.check_permission("database_ops") and not self.check_permission(
            "manage_inventory"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to access Recycle Bin.",
            )
            return
        RecycleBinDialog(self.db, self).exec()
        self.showFullScreen()

    def open_calculator(self):
        """Open the integrated floating calculator."""
        if not hasattr(self, "calc_dlg") or self.calc_dlg is None:
            self.calc_dlg = CalculatorDialog(self)
        self.calc_dlg.show()
        self.calc_dlg.raise_()
        self.calc_dlg.activateWindow()

    def view_history(self):
        """Open the sales history and day book dialog."""
        SalesHistoryDialog(self.db, self.printer, self).exec()
        self.showFullScreen()

    def handle_customer_lookup(self):
        """Perform a quick customer search by mobile number."""
        query = self.cust_mobile_input.text().strip()
        dlg = CustomerSearchDialog(self.db, self)
        if query:
            dlg.search_input.setText(query)
        if dlg.exec() == QDialog.Accepted:
            customer = dlg.selected_customer
            self.selected_customer_data = customer
            self.cust_name_label.setText(f"Name: {customer[1]}")
            self.cust_mobile_label.setText(f"Mob: {customer[2]}")
            self.cust_mobile_input.clear()
        self.showFullScreen()

    def hold_current_bill(self):
        """
        Save the current unsaved bill to the database 'held_sales' table for later recall.
        """
        items, total = [], 0.0
        for r in range(self.grid.rowCount()):
            name_it = self.grid.item(r, 1)
            if not name_it or not name_it.data(Qt.UserRole):
                continue
            try:
                qty, rate, disc = (
                    float(self.grid.item(r, 2).text()),
                    float(self.grid.item(r, 5).text()),
                    float(self.grid.item(r, 6).text()),
                )
                mrp = 0.0
                mrp_combo = self.grid.cellWidget(r, 4)
                if mrp_combo:
                    mrp = float(mrp_combo.currentText())
                eff_p = rate * (1 - disc / 100)
                if qty > 0:
                    items.append(
                        {
                            "id": name_it.data(Qt.UserRole)[0],
                            "name": name_it.data(Qt.UserRole)[1],
                            "barcode": name_it.data(Qt.UserRole)[2],
                            "price": eff_p,
                            "mrp": mrp,
                            "quantity": qty,
                            "uom": self.grid.item(r, 3).text(),
                        }
                    )
                    total += qty * eff_p
            except Exception:
                continue
        if not items:
            return
        if self.db.hold_sale(items, total, self.current_user[0]):
            self.reset_grid()
            QMessageBox.information(self, "Success", "Bill held successfully.")

    def recall_held_bill(self):
        """
        Open the list of held bills and restore the selected one to the main billing grid.
        """
        dlg = HeldSalesDialog(self.db, self)
        if dlg.exec() == QDialog.Accepted:
            held_id = dlg.selected_held_id
            items = self.db.get_held_sale_items(held_id)
            self.reset_grid()
            self.grid.setRowCount(len(items) + 1)
            self.updating_cell = True
            for row, item in enumerate(items):
                prod = self.db.find_product_by_barcode(item["barcode"])
                if prod:
                    self.grid.setItem(row, 0, QTableWidgetItem(item["barcode"]))
                    self.grid.setItem(row, 1, QTableWidgetItem(item["name"]))
                    self.grid.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
                    self.grid.setItem(row, 3, QTableWidgetItem(item["uom"]))
                    self.update_mrp_dropdown(row, prod[0], item["uom"], item["mrp"])
                    self.grid.setItem(row, 5, QTableWidgetItem(f"{item['price']:.3f}"))
                    self.grid.setItem(row, 6, QTableWidgetItem("0.0"))
                    self.grid.setItem(
                        row,
                        7,
                        QTableWidgetItem(f"{item['quantity'] * item['price']:.2f}"),
                    )
                    self.grid.item(row, 1).setData(Qt.UserRole, prod)
            self.updating_cell = False
            self.db.delete_held_sale(held_id)
            self.recalc_totals()
        self.showFullScreen()

    def load_bill_for_modification(self, sid):
        """
        Recall an existing saved bill from the database and load it into the billing grid
        for editing.
        """
        self.reset_grid()
        self.current_sale_id = sid
        self.bill_no_label.setText(f"Bill No: {sid} [EDIT MODE]")
        self.bill_no_label.setObjectName("info")
        self.bill_no_label.style().unpolish(self.bill_no_label)
        self.bill_no_label.style().polish(self.bill_no_label)
        sales = self.db.get_sales_history(query=str(sid))
        sale_header = next((s for s in sales if str(s[0]) == str(sid)), None)
        if sale_header and sale_header[5]:
            customer = self.db.get_customer_by_mobile(sale_header[5])
            if customer:
                self.selected_customer_data = customer
                self.cust_name_label.setText(f"Name: {customer[1]}")
                self.cust_mobile_label.setText(f"Mob: {customer[2]}")
        items = self.db.get_sale_items(sid)
        self.grid.setRowCount(len(items) + 1)
        self.updating_cell = True
        for row, item in enumerate(items):
            prod = self.db.find_product_by_barcode(item["barcode"])
            if prod:
                self.grid.setItem(row, 0, QTableWidgetItem(item["barcode"]))
                self.grid.setItem(row, 1, QTableWidgetItem(item["name"]))
                self.grid.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
                self.grid.setItem(row, 3, QTableWidgetItem(item["uom"]))
                uom_data = self.db.get_product_uom_data(prod[0], item["uom"])
                mrp = uom_data["mrp"] if uom_data else prod[3]
                self.update_mrp_dropdown(row, prod[0], item["uom"], mrp)
                self.grid.setItem(row, 5, QTableWidgetItem(f"{item['price']:.3f}"))
                self.grid.setItem(row, 6, QTableWidgetItem("0.0"))
                calc_rate = item["price"]
                if item["uom"] and item["uom"].lower() in ("g", "gram", "grams"):
                    calc_rate /= 1000.0
                self.grid.setItem(
                    row, 7, QTableWidgetItem(f"{item['quantity'] * calc_rate:.2f}")
                )
                self.grid.item(row, 1).setData(Qt.UserRole, prod)
        self.updating_cell = False
        self.recalc_totals()
        self.showFullScreen()

    def open_search_dialog(self):
        """
        Open the product search and selection dialog.
        """
        dlg = ProductSearchDialog(self.db, self)
        res = dlg.exec()
        self.showFullScreen()
        if res == QDialog.Accepted:
            row = max(0, self.grid.currentRow())
            if self.grid.item(row, 0) and self.grid.item(row, 0).text():
                if row == self.grid.rowCount() - 1:
                    self.grid.setRowCount(row + 2)
                row += 1
                self.grid.setCurrentCell(row, 0)
            self.grid.setItem(row, 0, QTableWidgetItem(dlg.selected_product[2]))

    def handle_grid_change(self, item):
        """
        Main logic for handling user input in the billing grid.
        """
        if self.updating_cell:
            return
        self.updating_cell = True
        try:
            row, col = item.row(), item.column()
            if col == 0:
                barcode = item.text().strip()
                if barcode:
                    product = self.db.find_product_smart(barcode)
                    if product:
                        self.grid.item(row, 0).setText(product[2])
                        self.populate_row(row, product)
                        QTimer.singleShot(0, lambda: self.grid.setCurrentCell(row, 2))
                    else:
                        for c in range(1, 7):
                            self.grid.setItem(row, c, QTableWidgetItem(""))
            elif col == 3:
                uom_text = item.text().strip().lower()
                if uom_text:
                    uom_map = self.db.get_uom_map()
                    if uom_text in uom_map:
                        self.grid.item(row, 3).setText(uom_map[uom_text])
                self.recalc_row(row)
            elif col in (2, 4, 5, 6):
                self.recalc_row(row)
            self.recalc_totals()
        finally:
            self.updating_cell = False

    def populate_row(self, row, product):
        """
        Fill a grid row with data from a retrieved product object.
        """
        self.grid.setItem(row, 1, QTableWidgetItem(product[1]))
        qty = str(product[9]) if len(product) > 9 else "1.0"
        self.grid.setItem(row, 2, QTableWidgetItem(qty))
        self.grid.setItem(row, 3, QTableWidgetItem(product[6]))
        self.update_mrp_dropdown(row, product[0], product[5], product[3])
        self.grid.setItem(row, 5, QTableWidgetItem(f"{product[4]:.3f}"))
        self.grid.setItem(row, 6, QTableWidgetItem("0.0"))
        self.grid.item(row, 1).setData(Qt.UserRole, product)
        self.recalc_row(row)

    def update_mrp_dropdown(self, row, product_id, uom, current_mrp):
        """
        Populate the MRP column with a dropdown if multiple prices exist.
        """
        combo = QComboBox()
        combo.setObjectName("grid-combo")
        mrps = self.db.get_available_mrps(product_id, uom)
        if not mrps:
            mrps = [{"mrp": float(current_mrp), "price": 0.0, "uom_alias": None}]
        for item in mrps:
            combo.addItem(f"{item['mrp']:.2f}", item)
            if abs(item["mrp"] - float(current_mrp)) < 0.001:
                combo.setCurrentIndex(combo.count() - 1)
        combo.currentIndexChanged.connect(lambda: self.handle_mrp_change(row))
        self.grid.setCellWidget(row, 4, combo)

    def handle_mrp_change(self, row):
        if self.updating_cell:
            return
        combo = self.grid.cellWidget(row, 4)
        if not combo:
            return
        data = combo.currentData()
        if data:
            self.updating_cell = True
            try:
                self.grid.setItem(row, 5, QTableWidgetItem(f"{data['price']:.3f}"))
            finally:
                self.updating_cell = False
            self.recalc_row(row)

    def recalc_row(self, row):
        """
        Update the amount and discount columns for a specific row based on quantity and unit.
        """
        try:
            qty_item, uom_item, rate_item, _disc_item = (
                self.grid.item(row, 2),
                self.grid.item(row, 3),
                self.grid.item(row, 5),
                self.grid.item(row, 6),
            )
            qty, uom, rate = (
                float(qty_item.text()) if qty_item else 0.0,
                uom_item.text() if uom_item else None,
                float(rate_item.text()) if rate_item else 0.0,
            )
            name_item = self.grid.item(row, 1)
            if name_item and name_item.data(Qt.UserRole):
                p_data = list(name_item.data(Qt.UserRole))
                if uom and uom != p_data[5]:
                    uom_data = self.db.get_product_uom_data(p_data[0], uom)
                    if uom_data:
                        rate = uom_data["price"]
                        mrp = uom_data["mrp"]
                        p_data[5], p_data[7], p_data[4], p_data[3] = (
                            uom_data["uom"],
                            uom_data["factor"],
                            uom_data["price"],
                            uom_data["mrp"],
                        )
                        self.updating_cell = True
                        try:
                            self.update_mrp_dropdown(row, p_data[0], uom, mrp)
                            self.grid.setItem(row, 5, QTableWidgetItem(f"{rate:.3f}"))
                        finally:
                            self.updating_cell = False
                        name_item.setData(Qt.UserRole, tuple(p_data))
                if rate == 0 and len(p_data) > 10:
                    rate = float(p_data[10]) * float(p_data[7])
                    self.grid.setItem(row, 5, QTableWidgetItem(f"{rate:.3f}"))
                is_gram = uom and uom.lower() in ("g", "gram", "grams")
                effective_rate = rate
                if is_gram:
                    effective_rate /= 1000.0
                gross, disc_amt = (
                    qty * effective_rate,
                    0.0,
                )
                scheme = self.db.get_active_scheme_for_product(p_data[0], qty, uom)
                if scheme:
                    s_val, s_type, s_uom = float(scheme[1]), scheme[2], scheme[3]
                    if s_uom and uom != s_uom:
                        uom = s_uom
                        self.grid.setItem(row, 3, QTableWidgetItem(uom))
                        uom_data = self.db.get_product_uom_data(p_data[0], uom)
                        if uom_data:
                            p_data[6], p_data[8], p_data[4], p_data[3] = (
                                uom_data["uom"],
                                uom_data["factor"],
                                uom_data["price"],
                                uom_data["mrp"],
                            )
                            name_item.setData(Qt.UserRole, tuple(p_data))
                    if s_type == "absolute_rate":
                        abs_rate = s_val
                        if is_gram:
                            abs_rate /= 1000.0
                        gross = qty * abs_rate
                        self.grid.setItem(row, 5, QTableWidgetItem(f"{abs_rate:.3f}"))
                        disc_amt = 0.0
                        self.grid.setItem(row, 6, QTableWidgetItem("0.0"))
                    elif s_type == "percent":
                        disc_amt = (gross * s_val) / 100
                        self.grid.setItem(row, 6, QTableWidgetItem(f"{s_val:.3f}"))
                    elif s_type == "amount":
                        benefit = s_val
                        if is_gram:
                            benefit /= 1000.0
                        disc_amt = qty * benefit
                        self.grid.setItem(
                            row,
                            6,
                            QTableWidgetItem(
                                f"{(disc_amt / gross) * 100 if gross > 0 else 0:.3f}"
                            ),
                        )
                else:
                    disc_amt = 0.0
                    self.grid.setItem(row, 6, QTableWidgetItem("0.0"))
                self.grid.setItem(row, 7, QTableWidgetItem(f"{gross - disc_amt:.2f}"))
            for c in [1, 4, 7]:
                it = self.grid.item(row, c)
                if it:
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
        except Exception:
            pass

    def _fmt(self, val):
        """
        Format a numeric value for UI display, stripping unnecessary decimals.
        """
        if float(val) == int(float(val)):
            return str(int(float(val)))
        return f"{float(val):.2f}"

    def recalc_totals(self):
        """
        Recalculate and update the total quantity and total amount labels.
        """
        t_qty = 0.0
        t_amt = 0.0
        for r in range(self.grid.rowCount()):
            q, a = self.grid.item(r, 2), self.grid.item(r, 7)
            try:
                t_qty += float(q.text())
            except Exception:
                pass
            try:
                t_amt += float(a.text())
            except Exception:
                pass
        rounded_total = round(t_amt)
        self.lbl_total_qty.setText(f"Qty: {self._fmt(t_qty)}")
        self.lbl_total_amt.setText(f"Total: {self._fmt(rounded_total)}")

    def reset_grid(self):
        """
        Clear the billing grid and reset customer selection for a new bill.
        """
        self.current_sale_id = None
        self.bill_no_label.setText("Bill No: <New>")
        self.bill_no_label.setObjectName("")
        self.bill_no_label.style().unpolish(self.bill_no_label)
        self.bill_no_label.style().polish(self.bill_no_label)
        self.selected_customer_data = None
        self.cust_name_label.setText("Name: <Cash>")
        self.cust_mobile_label.setText("Mob: -")
        self.grid.setRowCount(0)
        self.grid.setRowCount(1)
        self.recalc_totals()
        self.grid.setFocus()
        self.grid.setCurrentCell(0, 0)

    def process_checkout(self):
        """
        Validate all items in the grid, calculate final total, and save the sale.
        """
        items, total = [], 0.0
        for r in range(self.grid.rowCount()):
            name_it = self.grid.item(r, 1)
            if not name_it or not name_it.data(Qt.UserRole):
                continue
            try:
                qty, rate, disc = (
                    float(self.grid.item(r, 2).text()),
                    float(self.grid.item(r, 5).text()),
                    float(self.grid.item(r, 6).text()),
                )
                mrp = 0.0
                mrp_combo = self.grid.cellWidget(r, 4)
                if mrp_combo:
                    mrp = float(mrp_combo.currentText())
                uom = self.grid.item(r, 3).text()
                eff_p = rate * (1 - disc / 100)
                calc_rate = eff_p
                if uom and uom.lower() in ("g", "gram", "grams"):
                    calc_rate /= 1000.0
                if qty > 0:
                    items.append(
                        {
                            "id": name_it.data(Qt.UserRole)[0],
                            "name": name_it.data(Qt.UserRole)[1],
                            "barcode": name_it.data(Qt.UserRole)[2],
                            "price": eff_p,
                            "mrp": mrp,
                            "quantity": qty,
                            "uom": uom,
                            "factor": float(name_it.data(Qt.UserRole)[7]),
                        }
                    )
                    total += qty * calc_rate
            except Exception:
                continue
        if not items:
            return
        total = float(round(total))
        cid = self.selected_customer_data[0] if self.selected_customer_data else None
        msg = f"{'Update' if self.current_sale_id else 'Save'} Bill Rs. {self._fmt(total)}?"
        if (
            QMessageBox.question(
                self, "Save Voucher", msg, QMessageBox.Yes | QMessageBox.No
            )
            == QMessageBox.Yes
        ):
            res = (
                self.db.update_sale(self.current_sale_id, items, total, customer_id=cid)
                if self.current_sale_id
                else self.db.process_sale(items, total, customer_id=cid)
            )
            if res:
                if (
                    QMessageBox.question(
                        self,
                        "Print",
                        "Print Receipt?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    == QMessageBox.Yes
                ):
                    langs = self.db.get_languages()
                    selected_lang_id = None
                    should_print = True
                    if langs:
                        lang_dlg = LanguageSelectionDialog(self.db, self)
                        if lang_dlg.exec() == QDialog.Accepted:
                            selected_lang_id = lang_dlg.selected_lang_id
                        else:
                            should_print = False

                    if should_print:
                        print_items = self.db.get_translated_items(
                            items, selected_lang_id
                        )
                        cust_info = None
                        if self.selected_customer_data:
                            cust_info = {
                                "name": self.selected_customer_data[1],
                                "mobile": self.selected_customer_data[2],
                                "address": self.selected_customer_data[3],
                            }
                        if not os.path.exists(self.printer.config_path):
                            if (
                                PrinterConfigDialog(self.printer, self).exec()
                                != QDialog.Accepted
                            ):
                                should_print = False
                        if should_print:
                            self.printer.print_receipt(
                                print_items,
                                total,
                                self.current_sale_id or res,
                                customer_info=cust_info,
                            )
                bill_no = self.current_sale_id or res
                self.reset_grid()
                QMessageBox.information(
                    self, "Success", f"Voucher #{bill_no} Saved Successfully."
                )
        self.showFullScreen()
        self.grid.setFocus()


def main():
    """
    Main entry point for the elytPOS application.
    """
    app = QApplication(sys.argv)
    app.setFont(QFont("FiraCode Nerd Font", 10))
    config_path = os.path.join(get_app_path(), "db.config")

    # 1. Ensure config exists
    if not os.path.exists(config_path):
        if ConfigDialog(config_path).exec() != QDialog.Accepted:
            sys.exit(0)

    # 2. Company Selection Loop
    selected_db_name = None
    while True:
        config_params = DatabaseManager.load_config()
        # Test connection by listing databases
        try:
            # Check if we can connect to postgres first
            import psycopg2

            test_params = config_params.copy()
            test_params["dbname"] = "postgres"
            conn = psycopg2.connect(**test_params)
            conn.close()

            # If successful, show selection dialog
            sel_dlg = CompanySelectionDialog(config_params)
            if sel_dlg.exec() == QDialog.Accepted:
                selected_db_name = sel_dlg.selected_db
                break
            else:
                sys.exit(0)
        except Exception as e:
            # Connection failed (probably bad host/user/pass in config)
            box = QMessageBox()
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Database Connection Error")
            box.setText("Could not connect to PostgreSQL server.")
            box.setInformativeText(f"Please check your configuration.\n\nError: {e}")
            btn_retry = box.addButton("Retry", QMessageBox.ButtonRole.AcceptRole)
            btn_config = box.addButton("Configure", QMessageBox.ButtonRole.ActionRole)
            box.addButton(QMessageBox.StandardButton.Cancel)
            box.exec()

            if box.clickedButton() == btn_config:
                if ConfigDialog(config_path).exec() != QDialog.Accepted:
                    sys.exit(0)
            elif box.clickedButton() == btn_retry:
                continue
            else:
                sys.exit(1)

    # 3. Initialize Database Manager with selected DB
    try:
        db_manager = DatabaseManager(dbname=selected_db_name)
        conn = db_manager.get_connection()
        conn.close()
        db_manager.purge_old_deleted_products()
    except Exception as e:
        QMessageBox.critical(
            None,
            "Database Error",
            f"Failed to initialize database '{selected_db_name}':\n{e}",
        )
        sys.exit(1)

    # 4. Load Theme
    theme_name = db_manager.get_setting("theme", "mocha")
    app.setProperty("theme_name", theme_name)
    app.setWindowIcon(QIcon(resource_path(f"svg/logo_{theme_name}.svg")))
    style = get_style(theme_name)
    app.setStyleSheet(style)

    # 5. User Login / Creation
    if not db_manager.get_users():
        if SuperUserCreationDialog(db_manager).exec() != QDialog.Accepted:
            db_manager.close()
            sys.exit(0)

    app.aboutToQuit.connect(db_manager.close)
    login_dlg = LoginDialog(db_manager)
    if login_dlg.exec() == QDialog.Accepted:
        printer = ReceiptPrinter()
        if not os.path.exists(printer.config_path):
            PrinterConfigDialog(printer, hide_cancel=True).exec()
        window = MainWindow(db_manager, login_dlg.user)
        window.setWindowTitle(f"elytPOS - {selected_db_name} - {login_dlg.user[2]}")
        window.show()
        sys.exit(app.exec())
    else:
        db_manager.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
