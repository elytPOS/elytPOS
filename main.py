"""
Main entry point and GUI logic for elytPOS.
"""

import os
import sys
import subprocess

from PySide6.QtCore import Qt, QDate, QEvent, QTimer
from PySide6.QtGui import QFont, QAction, QKeyEvent, QPixmap, QIcon
from PySide6.QtWidgets import (
    QDateEdit,
    QComboBox,
    QStyledItemDelegate,
    QMainWindow,
    QPushButton,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QFormLayout,
    QGridLayout,
    QMenu,
    QMenuBar,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QGroupBox,
    QTabWidget,
    QWidget,
    QTextEdit,
    QApplication,
    QFileDialog,
    QInputDialog,
    QAbstractItemView,
    QCheckBox,
)

from database import DatabaseManager
from printer import ReceiptPrinter
from calculator_gui import CalculatorDialog
from help_system import HelpDialog, LicenseDialog
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
    Enhanced full-screen product search and selection interface.
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Product Selection")
        self.db = db_manager
        self.selected_product = None
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        layout = QVBoxLayout(self)

        title_lbl = QLabel("Product Search")
        title_lbl.setObjectName("title")
        layout.addWidget(title_lbl)

        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Type Name, Barcode, or Alias to Search (Esc to cancel)..."
        )
        self.search_input.setFixedHeight(50)
        self.search_input.setStyleSheet("font-size: 18pt; padding: 5px;")
        self.search_input.textChanged.connect(self.load_products)
        search_box.addWidget(self.search_input)

        layout.addLayout(search_box)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Barcode", "MRP", "Rate", "UOM", "Category"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.doubleClicked.connect(self.select_product)
        layout.addWidget(self.table)

        help_lbl = QLabel(
            "Use <b>Up/Down</b> to navigate, <b>Enter</b> to select, <b>Esc</b> to close."
        )
        layout.addWidget(help_lbl)

        self.load_products()
        self.search_input.setFocus()
        self.search_input.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.search_input:
            if event.key() == Qt.Key_Down:
                self.table.setFocus()
                if self.table.rowCount() > 0:
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
        query = self.search_input.text().strip()
        products = (
            self.db.search_products(query) if query else self.db.get_all_products()
        )

        self.table.setRowCount(0)
        for row, prod in enumerate(products):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod[1])))
            self.table.setItem(row, 1, QTableWidgetItem(str(prod[2])))
            self.table.setItem(row, 2, QTableWidgetItem(f"{float(prod[3]):.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{float(prod[4]):.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(prod[6])))
            self.table.setItem(row, 5, QTableWidgetItem(str(prod[5])))
            self.table.item(row, 0).setData(Qt.UserRole, prod)

    def select_product(self):
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
    Interface for creating and editing promotional schemes with an Excel-style grid.
    """

    def __init__(self, db_manager, scheme_id=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        title = "Modify Scheme" if scheme_id else "Add New Scheme"
        self.setWindowTitle(title)
        self.db, self.scheme_id = db_manager, scheme_id
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        header_frame = QFrame()
        header_frame.setObjectName("header-frame")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(15, 10, 15, 10)

        self.scheme_name = QLineEdit()
        self.scheme_name.setPlaceholderText("Scheme Name (e.g. Diwali Dhamaka)")
        self.scheme_name.setFixedHeight(40)
        self.scheme_name.setStyleSheet("font-size: 14pt; font-weight: bold;")

        self.valid_from = QDateEdit()
        self.valid_from.setDisplayFormat("dd-MM-yyyy")
        self.valid_from.setDate(QDate.currentDate())
        self.valid_from.setCalendarPopup(True)
        self.valid_from.setFixedHeight(40)

        self.valid_to = QDateEdit()
        self.valid_to.setDisplayFormat("dd-MM-yyyy")
        self.valid_to.setDate(QDate.currentDate().addDays(365))
        self.valid_to.setCalendarPopup(True)
        self.valid_to.setFixedHeight(40)

        h_layout.addWidget(QLabel("<b>SCHEME NAME:</b>"))
        h_layout.addWidget(self.scheme_name, 1)
        h_layout.addSpacing(20)
        h_layout.addWidget(QLabel("<b>VALID FROM:</b>"))
        h_layout.addWidget(self.valid_from)
        h_layout.addSpacing(10)
        h_layout.addWidget(QLabel("<b>TO:</b>"))
        h_layout.addWidget(self.valid_to)

        main_layout.addWidget(header_frame)

        grid_container = QVBoxLayout()
        grid_container.setContentsMargins(0, 10, 0, 10)

        self.items_list = QTableWidget()
        self.items_list.setColumnCount(9)
        self.items_list.setHorizontalHeaderLabels(
            [
                "Item Name",
                "ID",
                "MRP",
                "Min Qty",
                "Max Qty",
                "UOM",
                "Type",
                "Value",
                "Action",
            ]
        )
        self.items_list.setColumnHidden(1, True)
        self.items_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_list.verticalHeader().setDefaultSectionSize(40)
        self.items_list.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.items_list.itemChanged.connect(self.handle_item_change)
        self.items_list.setItemDelegateForColumn(
            0, FuzzyCompleterDelegate(self.db, self.items_list)
        )
        self.items_list.installEventFilter(self)
        grid_container.addWidget(self.items_list)

        main_layout.addLayout(grid_container)

        footer = QHBoxLayout()
        save_btn = QPushButton("SAVE SCHEME (F2)")
        save_btn.clicked.connect(self.save_scheme)
        save_btn.setObjectName("btnSave")
        save_btn.setFixedHeight(50)
        save_btn.setMinimumWidth(200)

        cancel_btn = QPushButton("CANCEL (Esc)")
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setObjectName("btnCancel")
        cancel_btn.setFixedHeight(50)

        footer.addStretch()
        footer.addWidget(save_btn)
        footer.addWidget(cancel_btn)
        main_layout.addLayout(footer)

        if self.scheme_id:
            self.load_scheme_data()
        else:
            self._add_row_to_table()

        s_f2 = QAction(self)
        s_f2.setShortcut("F2")
        s_f2.triggered.connect(self.save_scheme)
        self.addAction(s_f2)

        s_esc = QAction(self)
        s_esc.setShortcut("Esc")
        s_esc.triggered.connect(self.close)
        self.addAction(s_esc)

    def eventFilter(self, source, event):
        if source is self.items_list and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                row, col = self.items_list.currentRow(), self.items_list.currentColumn()
                if col == 0:
                    self.items_list.setCurrentCell(row, 3)
                elif col < 7:
                    self.items_list.setCurrentCell(row, col + 1)
                else:
                    if row == self.items_list.rowCount() - 1:
                        self._add_row_to_table()
                    self.items_list.setCurrentCell(row + 1, 0)
                return True
        return super().eventFilter(source, event)

    def handle_item_change(self, item):
        if item.column() == 0:
            row = item.row()
            text = item.text().strip()
            if not text:
                return

            prod = item.data(Qt.UserRole)
            if not prod:
                prod = self.db.find_product_smart(text)

            if prod:
                self.items_list.blockSignals(True)
                self.items_list.setItem(row, 1, QTableWidgetItem(str(prod[0])))
                self.items_list.setItem(
                    row, 2, QTableWidgetItem(f"{float(prod[3]):.3f}")
                )
                self.items_list.blockSignals(False)

    def _add_row_to_table(
        self,
        pname="",
        pid="",
        mrp=0.0,
        min_q=1.0,
        max_q=0.0,
        uom="<All UOMs>",
        b_idx=0,
        val=0.0,
    ):
        row = self.items_list.rowCount()
        self.items_list.insertRow(row)
        it_name = QTableWidgetItem(pname)
        it_name.setFlags(it_name.flags() & ~Qt.ItemIsEditable)
        it_name.setToolTip("Double-click to select item")
        self.items_list.setItem(row, 0, it_name)
        self.items_list.setItem(row, 1, QTableWidgetItem(str(pid)))
        self.items_list.setItem(row, 2, QTableWidgetItem(f"{float(mrp or 0):.3f}"))
        self.items_list.setItem(row, 3, QTableWidgetItem(f"{min_q:.3f}"))
        self.items_list.setItem(
            row, 4, QTableWidgetItem(f"{max_q:.3f}" if max_q > 0 else "∞")
        )
        uom_combo = QComboBox()
        uoms = ["<All UOMs>"] + [u[1] for u in self.db.get_uoms()]
        uom_combo.addItems(uoms)
        if isinstance(uom, str):
            idx = uom_combo.findText(uom)
            if idx >= 0:
                uom_combo.setCurrentIndex(idx)
        self.items_list.setCellWidget(row, 5, uom_combo)
        type_combo = QComboBox()
        type_combo.addItems(["Percent (%)", "Flat Amt (Rs)", "Fixed Rate"])
        type_combo.setCurrentIndex(b_idx)
        self.items_list.setCellWidget(row, 6, type_combo)
        self.items_list.setItem(row, 7, QTableWidgetItem(f"{val:.3f}"))
        del_btn = QPushButton("Del")
        del_btn.setObjectName("btnDelete")
        del_btn.clicked.connect(
            lambda: self.items_list.removeRow(self.items_list.currentRow())
        )
        self.items_list.setCellWidget(row, 8, del_btn)

    def load_scheme_data(self):
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
                float(r[8]) if r[8] is not None else 0.0,
                float(r[3]),
                float(r[4]) if r[4] else 0,
                r[5] or "<All UOMs>",
                b_idx,
                float(r[7]),
            )

    def save_scheme(self):
        name = self.scheme_name.text()
        if not name:
            QMessageBox.warning(self, "Error", "Scheme name is required.")
            return
        items_data = []
        for r in range(self.items_list.rowCount()):
            pid_item = self.items_list.item(r, 1)
            if not pid_item or not pid_item.text() or pid_item.text() == "None":
                continue

            mrp_item = self.items_list.item(r, 2)
            uom_widget = self.items_list.cellWidget(r, 5)
            uom_val = uom_widget.currentText() if uom_widget else "<All UOMs>"
            type_widget = self.items_list.cellWidget(r, 6)
            type_idx = type_widget.currentIndex() if type_widget else 0
            b_type = (
                "percent"
                if type_idx == 0
                else "amount"
                if type_idx == 1
                else "absolute_rate"
            )
            try:
                items_data.append(
                    {
                        "pid": int(pid_item.text()),
                        "mrp": float(mrp_item.text())
                        if mrp_item and mrp_item.text()
                        else None,
                        "min_qty": float(self.items_list.item(r, 3).text()),
                        "max_qty": (
                            float(self.items_list.item(r, 4).text())
                            if self.items_list.item(r, 4).text() != "∞"
                            else None
                        ),
                        "target_uom": (None if uom_val == "<All UOMs>" else uom_val),
                        "benefit_type": b_type,
                        "benefit_value": float(self.items_list.item(r, 7).text()),
                    }
                )
            except (ValueError, AttributeError):
                continue
        if not items_data:
            QMessageBox.warning(
                self, "Error", "At least one valid item rule is required."
            )
            return
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

        header = QLabel(
            "Modify Company Information" if self.is_modify else "Company Information"
        )
        header.setObjectName("title")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_general = QWidget()
        gen_layout = QFormLayout(self.tab_general)

        self.name_input = QLineEdit()
        self.print_name_input = QLineEdit()
        self.short_name_input = QLineEdit()

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

        self.name_input.textChanged.connect(
            lambda t: self.print_name_input.setText(t)
            if not self.print_name_input.isModified()
            else None
        )

        self.tabs.addTab(self.tab_general, "General")

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

        self.tab_currency = QWidget()
        curr_layout = QFormLayout(self.tab_currency)

        self.curr_symbol = QLineEdit("₹")
        self.curr_string = QLineEdit("Rupees")
        self.curr_sub_string = QLineEdit("Paise")

        curr_layout.addRow("Currency Symbol:", self.curr_symbol)
        curr_layout.addRow("Currency String:", self.curr_string)
        curr_layout.addRow("Sub String:", self.curr_sub_string)

        self.tabs.addTab(self.tab_currency, "Currency")

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
            self.fy_from.setEnabled(False)
            self.books_from.setEnabled(False)

        self.name_input.setFocus()

    def load_existing_data(self):
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
        try:

            def save(k, v):
                self.db.set_setting(k, str(v))

            save("company_name", self.name_input.text())
            save("print_name", self.print_name_input.text())
            save("short_name", self.short_name_input.text())

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
        dlg = CreateCompanyDialog(config_params=self.config_params, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.load_databases()
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

        copyright_label = QLabel("© 2026 Mohammed Adnan\nUnder GPLv3 License")
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

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        input_form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("(Leave blank to keep existing)")
        self.full_name = QLineEdit()
        self.role_combo = QComboBox()
        self.role_combo.addItems(["cashier", "manager", "admin"])
        self.role_combo.currentTextChanged.connect(self.on_role_change)

        input_form.addRow("Username:", self.username)
        input_form.addRow("Password:", self.password)
        input_form.addRow("Full Name:", self.full_name)
        input_form.addRow("Role:", self.role_combo)

        form_layout.addLayout(input_form)

        self.perm_grp = QGroupBox("Granular Permissions")
        p_layout = QGridLayout(self.perm_grp)
        self.check_boxes = {}

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
        defaults = {
            "cashier": ["billing", "view_reports"],
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

        targets = defaults.get(role, [])
        for key, cb in self.check_boxes.items():
            cb.setChecked(key in targets)

    def save_user(self):
        username = self.username.text().strip()
        if not username:
            return

        role = self.role_combo.currentText()
        pwd = self.password.text()

        if not pwd and not self.is_editing_mode():
            QMessageBox.warning(self, "Error", "Password required for new user.")
            return

        perms = {k: cb.isChecked() for k, cb in self.check_boxes.items()}

        if not pwd:
            QMessageBox.information(self, "Info", "Password not changed.")
            return

        if self.db.add_user(username, pwd, self.full_name.text(), role, perms):
            self.clear_form()
            self.load_users()
            QMessageBox.information(self, "Success", "User saved.")

    def is_editing_mode(self):
        current = self.username.text()
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).text() == current:
                return True
        return False

    def load_selected_user(self, item):
        row = item.row()
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
        self.on_role_change("cashier")  # Reset perms

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
        elif event.key() == Qt.Key_F10:
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
        save_btn = QPushButton("Save && &Connect")
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

        import crypto_utils

        crypto_utils.encrypt_file(self.config_path)

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


class ItemTranslationDialog(QDialog):
    """
    Interface for managing product name translations in multiple languages.
    """

    def __init__(self, db, product_id, product_name, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle(f"Translations: {product_name}")
        self.db, self.product_id = db, product_id
        self.showFullScreen()

        layout = QVBoxLayout(self)
        title = QLabel(f"Manage Translations: {product_name}")
        title.setObjectName("title")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.form = QFormLayout(content)
        self.inputs = {}

        langs = self.db.get_languages()
        cur_trans = self.db.get_translations(product_id)
        trans_map = {t[0]: t[2] for t in cur_trans}

        for lid, lname, lcode in langs:
            le = QLineEdit(trans_map.get(lid, ""))
            le.setPlaceholderText(f"Name in {lname}")
            self.inputs[lid] = le
            self.form.addRow(f"{lname} ({lcode}):", le)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save (F2)")
        save_btn.clicked.connect(self.save)
        save_btn.setObjectName("btnSave")
        close_btn = QPushButton("Close (Esc)")
        close_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        save_act = QAction(self)
        save_act.setShortcut("F2")
        save_act.triggered.connect(self.save)
        self.addAction(save_act)

        esc_act = QAction(self)
        esc_act.setShortcut("Esc")
        esc_act.triggered.connect(self.reject)
        self.addAction(esc_act)

    def save(self):
        for lid, le in self.inputs.items():
            val = le.text().strip()
            self.db.add_translation(self.product_id, lid, val)
        self.accept()


class InventoryDialog(QDialog):
    """
    Structured Item Master workflow:
    1. Search/Create Item (Name + Translations)
    2. Define Variants in Excel-like grid
    """

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Item Master")
        self.db = db_manager
        self.current_item_id = None
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        header_frame = QFrame()
        header_frame.setObjectName("header-frame")
        h_layout = QVBoxLayout(header_frame)

        item_info_row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name (e.g. Maggi Noodles)")
        self.name_input.setFixedHeight(40)
        self.name_input.setStyleSheet("font-size: 14pt; font-weight: bold;")

        self.search_btn = QPushButton(" Find Item (F10) ")
        self.search_btn.setFixedHeight(40)
        self.search_btn.clicked.connect(self.open_product_search)

        self.trans_btn = QPushButton(" Translations ")
        self.trans_btn.setFixedHeight(40)
        self.trans_btn.clicked.connect(self.open_translations)
        self.trans_btn.setEnabled(False)

        item_info_row.addWidget(QLabel("<b>ITEM NAME:</b>"))
        item_info_row.addWidget(self.name_input, 1)
        item_info_row.addWidget(self.search_btn)
        item_info_row.addWidget(self.trans_btn)
        h_layout.addLayout(item_info_row)

        main_layout.addWidget(header_frame)

        grid_container = QVBoxLayout()
        grid_container.setContentsMargins(0, 10, 0, 10)

        self.grid = QTableWidget()
        self.grid.setColumnCount(11)
        self.grid.setHorizontalHeaderLabels(
            [
                "ID",
                "Main Barcode",
                "Other Aliases/Shortcodes",
                "UOM",
                "MRP",
                "Selling Rate",
                "Purchase Price",
                "Factor",
                "Quantity",
                "Category",
                "Action",
            ]
        )
        self.grid.setColumnHidden(0, True)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grid.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.grid.verticalHeader().setDefaultSectionSize(40)
        self.grid.installEventFilter(self)
        grid_container.addWidget(self.grid)

        main_layout.addLayout(grid_container)

        footer = QHBoxLayout()
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet("font-weight: bold; color: #666;")

        self.save_btn = QPushButton("SAVE EVERYTHING (F2)")
        self.save_btn.clicked.connect(self.save_everything)
        self.save_btn.setObjectName("btnSave")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setMinimumWidth(200)

        close_btn = QPushButton("CLOSE (Esc)")
        close_btn.clicked.connect(self.close)
        close_btn.setObjectName("btnCancel")
        close_btn.setFixedHeight(50)

        footer.addWidget(self.status_lbl)
        footer.addStretch()
        footer.addWidget(self.save_btn)
        footer.addWidget(close_btn)
        main_layout.addLayout(footer)

        self.add_empty_variant_row()

        s_f2 = QAction(self)
        s_f2.setShortcut("F2")
        s_f2.triggered.connect(self.save_everything)
        self.addAction(s_f2)

        s_f10 = QAction(self)
        s_f10.setShortcut("F10")
        s_f10.triggered.connect(self.open_product_search)
        self.addAction(s_f10)

        s_esc = QAction(self)
        s_esc.setShortcut("Esc")
        s_esc.triggered.connect(self.close)
        self.addAction(s_esc)

    def _get_text(self, row, col):
        it = self.grid.item(row, col)
        return it.text().strip() if it else ""

    def open_product_search(self):
        dlg = ProductSearchDialog(self.db, self)
        if dlg.exec() == QDialog.Accepted:
            prod = dlg.selected_product
            self.current_item_id = prod[0]
            self.name_input.setText(prod[1])
            self.trans_btn.setEnabled(True)
            self.load_variants()
        self.showFullScreen()

    def load_variants(self):
        self.grid.setRowCount(0)
        p = self.db.get_product_by_id(self.current_item_id)
        if p:
            self.add_variant_to_grid(p, is_base=True)
        aliases = self.db.get_aliases(self.current_item_id)
        for a in aliases:
            self.add_variant_to_grid(a, is_base=False)
        self.add_empty_variant_row()
        self.status_lbl.setText(f"Loaded item: {p[1]}")

    def add_variant_to_grid(self, data, is_base=True):
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        self.grid.setItem(row, 0, QTableWidgetItem(str(data[0])))
        self.grid.setItem(row, 1, QTableWidgetItem(str(data[2])))  # barcode
        self.grid.setItem(
            row, 2, QTableWidgetItem(str(data[7 if is_base else 7] or ""))
        )  # aliases
        self.grid.setItem(row, 3, QTableWidgetItem(str(data[6 if is_base else 2])))
        self.grid.setItem(
            row, 4, QTableWidgetItem(f"{float(data[3 if is_base else 3]):.2f}")
        )
        self.grid.setItem(
            row, 5, QTableWidgetItem(f"{float(data[4 if is_base else 4]):.2f}")
        )
        self.grid.setItem(
            row, 6, QTableWidgetItem(f"{float(data[8 if is_base else 8]):.2f}")
        )
        self.grid.setItem(
            row, 7, QTableWidgetItem(f"{float(1.0 if is_base else data[5]):.3f}")
        )
        self.grid.setItem(
            row, 8, QTableWidgetItem(f"{float(data[9] if is_base else 1.0):.2f}")
        )
        self.grid.setItem(row, 9, QTableWidgetItem(str(data[5] if is_base else "")))
        d_btn = QPushButton("Del")
        d_btn.setObjectName("btnDelete")
        if is_base:
            d_btn.setEnabled(False)
        d_btn.clicked.connect(self.handle_delete_variant)
        self.grid.setCellWidget(row, 10, d_btn)

    def add_empty_variant_row(self):
        row = self.grid.rowCount()
        self.grid.insertRow(row)
        for c in range(10):
            self.grid.setItem(row, c, QTableWidgetItem(""))
        self.grid.item(row, 4).setText("0.00")
        self.grid.item(row, 5).setText("0.00")
        self.grid.item(row, 6).setText("0.00")
        self.grid.item(row, 7).setText("1.000")
        self.grid.item(row, 8).setText("1.00")

    def handle_delete_variant(self):
        btn = self.sender()
        if btn:
            row = self.grid.indexAt(btn.pos()).row()
            self.grid.removeRow(row)

    def open_translations(self):
        if self.current_item_id:
            ItemTranslationDialog(
                self.db, self.current_item_id, self.name_input.text(), self
            ).exec()
            self.showFullScreen()

    def save_everything(self):
        item_name = self.name_input.text().strip()
        if not item_name:
            QMessageBox.warning(self, "Error", "Item Name is required.")
            return
        try:
            r0 = 0
            if self.grid.rowCount() == 0:
                self.add_empty_variant_row()

            barcode = self._get_text(r0, 1)
            aliases_str = self._get_text(r0, 2)
            uom = self._get_text(r0, 3) or "pcs"
            mrp = float(self._get_text(r0, 4) or 0)
            rate = float(self._get_text(r0, 5) or 0)
            pur = float(self._get_text(r0, 6) or 0)
            load_qty = float(self._get_text(r0, 8) or 1.0)
            cat = self._get_text(r0, 9) or "General"

            all_input_barcodes = set()
            if barcode:
                all_input_barcodes.add(barcode)
            for a in aliases_str.split(","):
                a = a.strip()
                if a:
                    if a in all_input_barcodes:
                        QMessageBox.warning(
                            self, "Error", f"Duplicate alias found in input: {a}"
                        )
                        return
                    all_input_barcodes.add(a)

            for b in all_input_barcodes:
                collision = self.db.check_alias_exists(
                    b, exclude_product_id=self.current_item_id
                )
                if collision:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Barcode/Alias '{b}' already assigned to {collision}",
                    )
                    return

            if self.current_item_id:
                self.db.update_product(
                    self.current_item_id,
                    item_name,
                    barcode,
                    mrp,
                    rate,
                    cat,
                    uom,
                    aliases_str,
                    pur,
                    load_qty,
                )
            else:
                self.current_item_id = self.db.add_product(
                    item_name, barcode, mrp, rate, cat, uom, aliases_str, pur, load_qty
                )
                self.trans_btn.setEnabled(True)

            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM product_aliases WHERE product_id = %s",
                (self.current_item_id,),
            )
            conn.commit()

            for r in range(1, self.grid.rowCount()):
                v_bar = self._get_text(r, 1)
                if not v_bar:
                    continue
                v_aliases_str = self._get_text(r, 2)

                variant_barcodes = set()
                variant_barcodes.add(v_bar)
                for a in v_aliases_str.split(","):
                    a = a.strip()
                    if a:
                        if a in variant_barcodes or a in all_input_barcodes:
                            QMessageBox.warning(
                                self, "Error", f"Duplicate alias found in variants: {a}"
                            )
                            return
                        variant_barcodes.add(a)

                for b in variant_barcodes:
                    collision = self.db.check_alias_exists(
                        b, exclude_product_id=self.current_item_id
                    )
                    if collision:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"Variant Barcode/Alias '{b}' already assigned to {collision}",
                        )
                        return

                all_input_barcodes.update(variant_barcodes)

                v_uom = self._get_text(r, 3)
                v_mrp = float(self._get_text(r, 4) or 0)
                v_rate = float(self._get_text(r, 5) or 0)
                v_pur = float(self._get_text(r, 6) or 0)
                v_fact = float(self._get_text(r, 7) or 1.0)
                v_stock = float(self._get_text(r, 8) or 0)
                self.db.add_alias(
                    self.current_item_id,
                    v_bar,
                    v_uom,
                    v_mrp,
                    v_rate,
                    v_fact,
                    1.0,
                    v_aliases_str,
                    v_pur,
                    v_stock,
                )

            QMessageBox.information(
                self, "Success", f"Item '{item_name}' and variants saved."
            )
            self.status_lbl.setText("Saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def eventFilter(self, source, event):
        if source is self.grid and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                row, col = self.grid.currentRow(), self.grid.currentColumn()
                if col < 9:
                    self.grid.setCurrentCell(row, col + 1)
                else:
                    if row == self.grid.rowCount() - 1:
                        self.add_empty_variant_row()
                    self.grid.setCurrentCell(row + 1, 1)
                return True
        return super().eventFilter(source, event)


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
        self.table.verticalHeader().setDefaultSectionSize(40)  # Increased row height
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
        self.setColumnWidth(0, 160)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in [2, 3, 4, 5, 6, 7]:
            self.setColumnWidth(i, 80)

        self.verticalHeader().setDefaultSectionSize(35)  # Taller rows
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
        if self.state() == QAbstractItemView.EditingState:
            super().keyPressEvent(event)
            return

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
        self.column_idx = 0
        self.selected_product = None
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

    def set_column_context(self, col):
        self.column_idx = col

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
                label = f"{p[1]} | {p[6]} | Qty: {p[7]:.2f} | MRP: {p[3]:.2f}"
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, p)
                self.popup.addItem(item)
            self.popup.setCurrentRow(0)
            self.popup.setFixedWidth(max(self.width() + 50, 450))
            self.popup.setFixedHeight(min(self.popup.count() * 38 + 5, 350))
            pos = self.mapToGlobal(self.rect().bottomLeft())
            self.popup.move(pos)
            self.popup.show()
        except Exception as e:
            print(f"Fuzzy search error: {e}")
            pass

    def on_item_clicked(self, item):
        """
        Handle item selection from the search results popup.
        """
        self.selected_product = item.data(Qt.UserRole)
        p = self.selected_product

        parent_table = self.parent().parent()
        if isinstance(parent_table, QTableWidget):
            row = parent_table.currentRow()
            cur_it = parent_table.item(row, 0)
            if not cur_it:
                cur_it = QTableWidgetItem()
                parent_table.setItem(row, 0, cur_it)
            cur_it.setData(Qt.UserRole, p)

        if isinstance(parent_table, QTableWidget):
            header_label = parent_table.horizontalHeaderItem(0).text()
            if "Barcode" in header_label:
                self.setText(p[2])  # Barcode
            else:
                self.setText(p[1])  # Name
        else:
            self.setText(p[2])

        self.popup.hide()
        self.returnPressed.emit()

    def keyPressEvent(self, event):
        """
        Override key events to handle navigation within the search popup.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.popup.isVisible() and self.popup.currentRow() >= 0:
                self.on_item_clicked(self.popup.currentItem())
                return

            if self.text().strip() == "":
                try:
                    table = self.parent().parent()
                    window = table.window()
                    if hasattr(window, "open_search_dialog"):
                        self.popup.hide()
                        window.open_search_dialog()
                        return
                except Exception:
                    pass

            self.popup.hide()
            self.returnPressed.emit()
            return

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
            if event.key() == Qt.Key_Tab:
                if self.popup.currentRow() >= 0:
                    self.on_item_clicked(self.popup.currentItem())
                self.popup.hide()
                super().keyPressEvent(event)
                return
            if event.key() == Qt.Key_Escape:
                self.popup.hide()
                return

        super().keyPressEvent(event)

    def hideEvent(self, event):
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
            editor = FuzzySearchLineEdit(self.db, parent)
            editor.set_column_context(index.column())
            return editor
        return super().createEditor(parent, option, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, FuzzySearchLineEdit) and editor.selected_product:
            model.setData(index, editor.selected_product, Qt.UserRole)
        super().setModelData(editor, model, index)


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
        self.currency_symbol = self.db.get_setting("currency_symbol", "₹")
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

        for widget in app.topLevelWidgets():
            widget.setStyleSheet(style)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self.db.set_setting("theme", theme_name)
        self.update_total_label_style()

    def check_permission(self, perm_key):
        import json

        try:
            if not self.current_user or len(self.current_user) < 5:
                return False

            perms_str = self.current_user[4]
            if not perms_str:
                role = self.current_user[3]
                if role == "admin":
                    return True
                defaults = {
                    "staff": ["billing", "view_reports"],
                    "cashier": ["billing", "view_reports"],
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
        company_name = self.db.get_setting("company_name", "elytPOS System")
        fy_start = self.db.get_setting("books_start", "2026-04-01")
        try:
            year = fy_start.split("-")[0]
            fy_str = f"{year}-{int(year) + 1}"
        except Exception:
            fy_str = "2026-2027"

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        menubar = QMenuBar()
        menubar.setNativeMenuBar(False)
        menubar.setFont(QFont("FiraCode Nerd Font", 10))
        layout.addWidget(menubar)

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

        tools_menu = menubar.addMenu("&Tools")
        calc_action = QAction("&Calculator (F8)", self)
        calc_action.setShortcuts(["Ctrl+Alt+C", "F8"])
        calc_action.triggered.connect(self.open_calculator)
        tools_menu.addAction(calc_action)

        if self.check_permission("database_ops"):
            tools_menu.addAction("&Maintenance", self.open_maintenance)
            tools_menu.addAction("&Recycle Bin", self.open_recycle_bin)

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

        license_action = QAction("&License", self)
        license_action.triggered.connect(self.open_license)
        help_menu.addAction(license_action)

        top_bar = QFrame()
        top_bar.setObjectName("header-frame")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 10, 15, 10)

        date_grp = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(False)
        self.date_edit.setFixedWidth(130)
        self.date_edit.setFixedHeight(35)

        self.bill_no_label = QLabel("<b>NEW BILL</b>")
        self.bill_no_label.setStyleSheet(
            "color: #40a02b; font-size: 16px; font-weight: bold; background: #e6f4ea; padding: 5px 10px; border-radius: 4px;"
        )

        date_grp.addWidget(QLabel("<b>DATE:</b>"))
        date_grp.addWidget(self.date_edit)
        date_grp.addSpacing(20)
        date_grp.addWidget(QLabel("<b>BILL NO:</b>"))
        date_grp.addWidget(self.bill_no_label)
        top_layout.addLayout(date_grp)
        top_layout.addStretch()

        comp_lbl = QLabel(f"<b>{company_name}</b> | FY: {fy_str}")
        comp_lbl.setStyleSheet("font-size: 14px; opacity: 0.8;")
        top_layout.addWidget(comp_lbl)

        layout.addWidget(top_bar)

        cust_frame = QFrame()
        cust_frame.setStyleSheet(
            "background-color: rgba(0,0,0,0.03); border-radius: 8px; margin: 5px 0;"
        )
        cust_layout = QHBoxLayout(cust_frame)
        cust_layout.setContentsMargins(15, 10, 15, 10)

        self.cust_mobile_input = QLineEdit()
        self.cust_mobile_input.setPlaceholderText("Customer Mobile / ID (F3)")
        self.cust_mobile_input.setFixedWidth(250)
        self.cust_mobile_input.setFixedHeight(45)
        self.cust_mobile_input.setStyleSheet(
            "font-size: 14pt; padding: 5px; border: 2px solid #ccc;"
        )
        self.cust_mobile_input.returnPressed.connect(self.handle_customer_lookup)

        self.cust_name_label = QLabel("Walk-in Customer")
        self.cust_name_label.setStyleSheet(
            "font-weight: 900; font-size: 18pt; color: #1e66f5; margin-left: 20px;"
        )
        self.cust_mobile_label = QLabel("")
        self.cust_mobile_label.setStyleSheet(
            "font-size: 14pt; color: #666; margin-left: 10px;"
        )

        self.selected_customer_data = None

        cust_layout.addWidget(QLabel("<b>CUSTOMER:</b>"))
        cust_layout.addWidget(self.cust_mobile_input)
        cust_layout.addWidget(self.cust_name_label)
        cust_layout.addWidget(self.cust_mobile_label)
        cust_layout.addStretch()

        layout.addWidget(cust_frame)

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
        btn_f10 = QPushButton("S&earch (F10)")
        btn_f10.clicked.connect(self.open_search_dialog)
        btn_f3 = QPushButton("C&ust (F3)")
        btn_f3.clicked.connect(self.open_customer_search)
        btn_f4 = QPushButton("C&lear (F4)")
        btn_f4.clicked.connect(self.reset_grid)

        btn_more = QPushButton("More...")
        more_menu = QMenu(self)

        act_history = QAction("&History (F5)", self)
        act_history.triggered.connect(self.view_history)
        more_menu.addAction(act_history)

        act_hold = QAction("&Hold (F6)", self)
        act_hold.triggered.connect(self.hold_current_bill)
        more_menu.addAction(act_hold)

        act_recall = QAction("&Recall (F7)", self)
        act_recall.triggered.connect(self.recall_held_bill)
        more_menu.addAction(act_recall)

        act_calc = QAction("Ca&lc (F8)", self)
        act_calc.triggered.connect(self.open_calculator)
        more_menu.addAction(act_calc)

        btn_more.setMenu(more_menu)

        btn_esc = QPushButton("&Quit (Esc)")
        btn_esc.clicked.connect(self.close)

        btn_layout.addWidget(btn_f2)
        btn_layout.addWidget(btn_f10)
        btn_layout.addWidget(btn_f3)
        btn_layout.addWidget(btn_f4)
        btn_layout.addWidget(btn_more)
        btn_layout.addWidget(btn_esc)
        self.lbl_total_amt = QLabel("Total: 0.00")
        self.update_total_label_style()
        footer.addLayout(btn_layout)
        footer.addStretch()
        footer.addSpacing(20)
        footer.addWidget(self.lbl_total_amt)
        layout.addLayout(footer)
        self.grid.setFocus()
        self.grid.setCurrentCell(0, 0)
        c_shortcut = QAction(self)
        c_shortcut.setShortcut("F3")
        c_shortcut.triggered.connect(self.open_customer_search)
        self.addAction(c_shortcut)
        s_shortcut = QAction(self)
        s_shortcut.setShortcut("F10")
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
        HelpDialog(self).exec()

    def open_license(self):
        LicenseDialog(self).exec()

    def open_scheme_entry(self, sid=None):
        if not self.check_permission("manage_schemes"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Schemes."
            )
            return

        if sid is None:
            name, ok = QInputDialog.getText(self, "New Scheme", "Enter Scheme Name:")
            if not ok or not name.strip():
                return
            dlg = SchemeEntryDialog(self.db, sid, self)
            dlg.scheme_name.setText(name)
            dlg.exec()
        else:
            SchemeEntryDialog(self.db, sid, self).exec()
        self.showFullScreen()

    def open_scheme_list(self, mode):
        if not self.check_permission("manage_schemes"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Schemes."
            )
            return
        SchemeListDialog(self.db, mode, self).exec()
        self.showFullScreen()

    def open_customer_master(self):
        if not self.check_permission("manage_customers"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Customers."
            )
            return
        CustomerMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_customer_search(self):
        dlg = CustomerSearchDialog(self.db, self)
        if dlg.exec() == QDialog.Accepted:
            customer = dlg.selected_customer
            self.selected_customer_data = customer
            self.cust_name_label.setText(f"Name: {customer[1]}")
            self.cust_mobile_label.setText(f"Mob: {customer[2]}")
            self.cust_mobile_input.clear()
        self.showFullScreen()

    def open_purchase_master(self):
        if not self.check_permission("manage_purchases"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Purchases."
            )
            return
        PurchaseEntryDialog(self.db, self).exec()
        self.showFullScreen()

    def open_inventory(self):
        if not self.check_permission("manage_inventory"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Inventory."
            )
            return
        InventoryDialog(self.db, self).exec()
        self.showFullScreen()

    def open_uom_master(self):
        if not self.check_permission("manage_inventory"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage UOMs."
            )
            return
        UOMMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_language_master(self):
        if not self.check_permission("manage_inventory"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Languages."
            )
            return
        LanguageMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_create_company(self):
        if not self.check_permission("settings") and not self.check_permission(
            "database_ops"
        ):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to Create Companies."
            )
            return
        CreateCompanyDialog(config_params=self.db.conn_params, parent=self).exec()
        self.showFullScreen()

    def open_modify_company(self):
        if not self.check_permission("settings"):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to Modify Company Settings.",
            )
            return
        CreateCompanyDialog(self.db.conn_params, db_manager=self.db, parent=self).exec()
        self.printer.load_from_db()
        self.showFullScreen()

    def open_user_master(self):
        if not self.check_permission("manage_users"):
            QMessageBox.warning(
                self, "Access Denied", "You do not have permission to manage Users."
            )
            return
        UserMasterDialog(self.db, self).exec()
        self.showFullScreen()

    def open_maintenance(self):
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
        if not hasattr(self, "calc_dlg") or self.calc_dlg is None:
            self.calc_dlg = CalculatorDialog(self)
        self.calc_dlg.show()
        self.calc_dlg.raise_()
        self.calc_dlg.activateWindow()

    def view_history(self):
        SalesHistoryDialog(self.db, self.printer, self).exec()
        self.showFullScreen()

    def handle_customer_lookup(self):
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
                    self.update_uom_dropdown(row, prod[0], item["uom"])
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
        self.bill_no_label.setText(f"<b>{sid}</b> [EDIT MODE]")
        self.bill_no_label.setObjectName("info")
        self.bill_no_label.style().unpolish(self.bill_no_label)
        self.bill_no_label.style().polish(self.bill_no_label)
        sales = self.db.get_sales_history(query=str(sid))
        sale_header = next((s for s in sales if str(s[0]) == str(sid)), None)
        if sale_header:
            if sale_header[1]:
                self.date_edit.setDate(sale_header[1].date())

            if sale_header[5]:
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

                self.update_uom_dropdown(row, prod[0], item["uom"])

                mrp = item.get("mrp")
                if not mrp:
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
                    product = item.data(Qt.UserRole)

                    if not product:
                        product = self.db.find_product_smart(barcode)

                    if product:
                        if item.text() != str(product[2]):
                            item.setText(str(product[2]))
                        self.populate_row(row, product)
                        QTimer.singleShot(0, lambda: self.grid.setCurrentCell(row, 2))
                    else:
                        for c in range(1, 7):
                            it = self.grid.item(row, c)
                            if it:
                                it.setText("")
            elif col == 3:
                uom_text = item.text().strip().lower()
                if uom_text:
                    uom_map = self.db.get_uom_map()
                    if uom_text in uom_map:
                        uom_text = uom_map[uom_text]
                        self.grid.item(row, 3).setText(uom_text)

                    name_it = self.grid.item(row, 1)
                    if name_it:
                        prod = name_it.data(Qt.UserRole)
                        if prod:
                            uom_data = self.db.get_product_uom_data(prod[0], uom_text)
                            if uom_data:
                                self.grid.setItem(
                                    row, 5, QTableWidgetItem(f"{uom_data['price']:.3f}")
                                )
                                self.update_mrp_dropdown(
                                    row, prod[0], uom_text, uom_data["mrp"]
                                )
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
        try:
            name = str(product[1])
            mrp = float(product[3])
            price = float(product[4])
            uom = str(product[6])

            qty = 1.0
            if len(product) == 8:
                qty = float(product[7])
            elif len(product) >= 10:
                qty = float(product[9])

            self.grid.setItem(row, 1, QTableWidgetItem(name))
            self.grid.setItem(row, 2, QTableWidgetItem(f"{qty:.2f}"))

            self.update_uom_dropdown(row, product[0], uom)

            self.update_mrp_dropdown(row, product[0], uom, mrp)
            self.grid.setItem(row, 5, QTableWidgetItem(f"{price:.3f}"))
            self.grid.setItem(row, 6, QTableWidgetItem("0.0"))

            self.grid.item(row, 1).setData(Qt.UserRole, product)
            self.recalc_row(row)
        except Exception as e:
            print(f"Error populating row {row}: {e}")

    def update_uom_dropdown(self, row, product_id, current_uom):
        combo = QComboBox()
        combo.setObjectName("grid-combo")
        units = self.db.get_product_units(product_id)

        if not units:
            units = [{"uom": current_uom, "price": 0.0, "mrp": 0.0}]

        for item in units:
            combo.addItem(str(item["uom"]), item)
            if item["uom"] == current_uom:
                combo.setCurrentIndex(combo.count() - 1)

        combo.currentIndexChanged.connect(lambda: self.handle_uom_change(row))
        self.grid.setCellWidget(row, 3, combo)

    def handle_uom_change(self, row):
        if self.updating_cell:
            return
        combo = self.grid.cellWidget(row, 3)
        if not combo:
            return
        data = combo.currentData()
        if data:
            self.updating_cell = True
            try:
                self.grid.setItem(row, 5, QTableWidgetItem(f"{data['price']:.3f}"))

                name_it = self.grid.item(row, 1)
                if name_it:
                    prod = name_it.data(Qt.UserRole)
                    if prod:
                        self.update_mrp_dropdown(row, prod[0], data["uom"], data["mrp"])
            finally:
                self.updating_cell = False
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
                if data.get("price") and data["price"] > 0:
                    self.grid.setItem(row, 5, QTableWidgetItem(f"{data['price']:.3f}"))
            finally:
                self.updating_cell = False
            self.recalc_row(row)

    def recalc_row(self, row):
        """
        Update the amount and discount columns for a specific row based on quantity and unit.
        """
        try:
            qty_item, rate_item, _disc_item = (
                self.grid.item(row, 2),
                self.grid.item(row, 5),
                self.grid.item(row, 6),
            )

            uom = ""
            uom_combo = self.grid.cellWidget(row, 3)
            if uom_combo:
                uom = uom_combo.currentText()
            else:
                uom_item = self.grid.item(row, 3)
                if uom_item:
                    uom = uom_item.text()

            qty, rate = (
                float(qty_item.text()) if qty_item else 0.0,
                float(rate_item.text()) if rate_item else 0.0,
            )

            mrp = 0.0
            mrp_combo = self.grid.cellWidget(row, 4)
            if mrp_combo:
                try:
                    mrp = float(mrp_combo.currentText())
                except ValueError:
                    mrp = 0.0

            name_item = self.grid.item(row, 1)
            if name_item and name_item.data(Qt.UserRole):
                p_data = list(name_item.data(Qt.UserRole))

                if mrp == 0 and len(p_data) > 3:
                    mrp = float(p_data[3])

                if uom and uom != p_data[6]:
                    uom_data = self.db.get_product_uom_data(p_data[0], uom)
                    if uom_data:
                        rate = uom_data["price"]
                        mrp = uom_data["mrp"]
                        p_data[6], p_data[7], p_data[4], p_data[3] = (
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
                scheme = self.db.get_active_scheme_for_product(p_data[0], qty, uom, mrp)
                if scheme:
                    s_val, s_type, s_uom = float(scheme[1]), scheme[2], scheme[3]
                    if s_uom and uom != s_uom:
                        uom = s_uom
                        self.grid.setItem(row, 3, QTableWidgetItem(uom))
                        uom_data = self.db.get_product_uom_data(p_data[0], uom)
                        if uom_data:
                            p_data[6], p_data[7], p_data[4], p_data[3] = (
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
        self.lbl_total_amt.setText(
            f"Total: {self.currency_symbol} {self._fmt(rounded_total)}"
        )

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

                uom = ""
                factor = 1.0
                uom_combo = self.grid.cellWidget(r, 3)
                if uom_combo:
                    uom = uom_combo.currentText()
                    uom_data = uom_combo.currentData()
                    if uom_data:
                        factor = float(uom_data.get("factor", 1.0))

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
                            "factor": factor,
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
    enc_path = config_path + ".enc"

    if not os.path.exists(config_path) and not os.path.exists(enc_path):
        if ConfigDialog(config_path).exec() != QDialog.Accepted:
            sys.exit(0)

    selected_db_name = None
    while True:
        config_params = DatabaseManager.load_config()
        try:
            import psycopg2

            test_params = config_params.copy()
            test_params["dbname"] = "postgres"
            conn = psycopg2.connect(**test_params)
            conn.close()

            sel_dlg = CompanySelectionDialog(config_params)
            if sel_dlg.exec() == QDialog.Accepted:
                selected_db_name = sel_dlg.selected_db
                break
            else:
                sys.exit(0)
        except Exception as e:
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

    theme_name = db_manager.get_setting("theme", "mocha")
    app.setProperty("theme_name", theme_name)
    app.setWindowIcon(QIcon(resource_path(f"svg/logo_{theme_name}.svg")))
    style = get_style(theme_name)
    app.setStyleSheet(style)

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
