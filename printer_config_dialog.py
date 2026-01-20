from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox, 
                               QPushButton, QMessageBox, QTabWidget, QWidget, QLineEdit, 
                               QTextEdit, QCheckBox, QHBoxLayout)
from PySide6.QtCore import Qt
from styles import MODERN_STYLE
class PrinterConfigDialog(QDialog):
    def __init__(self, printer_manager, parent=None, hide_cancel=False):
        super().__init__(parent)
        self.setWindowTitle("Printer Configuration")
        self.hide_cancel = hide_cancel
        if hide_cancel:
            self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.printer_manager = printer_manager
        self.config = self.printer_manager.load_config()
        layout = QVBoxLayout(self)
        title = QLabel("Printer & Receipt Setup")
        title.setObjectName("title")
        layout.addWidget(title, 0, Qt.AlignCenter)
        self.tabs = QTabWidget()
        self.setup_printer_tab()
        self.setup_content_tab()
        self.setup_options_tab()
        layout.addWidget(self.tabs)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        if hide_cancel:
            self.cancel_btn.hide()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("btnSave")
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        self.setFixedWidth(450)
        self.setFixedHeight(500)
    def setup_printer_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        self.printer_combo = QComboBox()
        self.available_printers = self.printer_manager.get_available_printers()
        self.printer_combo.addItems(self.available_printers)
        current_printer = self.config.get("printer_name")
        if current_printer in self.available_printers:
            self.printer_combo.setCurrentText(current_printer)
        self.paper_width = QComboBox()
        self.paper_width.addItems(["58mm", "76mm", "80mm"])
        self.paper_width.setCurrentText(self.config.get("paper_width", "76mm"))
        self.font_size = QComboBox()
        self.font_size.addItems(["Small", "Medium", "Large"])
        self.font_size.setCurrentText(self.config.get("font_size", "Medium"))
        form.addRow("Printer:", self.printer_combo)
        form.addRow("Paper Width:", self.paper_width)
        form.addRow("Font Size:", self.font_size)
        self.tabs.addTab(tab, "Printer")
    def setup_content_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        self.header_text = QLineEdit(self.config.get("header_text", "ELYT POS"))
        self.shop_name = QLineEdit(self.config.get("shop_name", "KIRANA STORE"))
        self.tax_id = QLineEdit(self.config.get("tax_id", ""))
        self.tax_id.setPlaceholderText("GST Number")
        self.footer_text = QTextEdit()
        self.footer_text.setPlainText(self.config.get("footer_text", "Thank you!").replace("<br/>", "\n"))
        self.footer_text.setFixedHeight(80)
        form.addRow("Header Title:", self.header_text)
        form.addRow("Shop Name:", self.shop_name)
        form.addRow("GST Number:", self.tax_id)
        form.addRow("Footer Text:", self.footer_text)
        self.tabs.addTab(tab, "Content")
    def setup_options_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.show_savings = QCheckBox("Show 'Total Savings' on Receipt")
        self.show_savings.setChecked(self.config.get("show_savings", True))
        self.show_mrp = QCheckBox("Show MRP for Items")
        self.show_mrp.setChecked(self.config.get("show_mrp", True))
        layout.addWidget(self.show_savings)
        layout.addWidget(self.show_mrp)
        layout.addStretch()
        self.tabs.addTab(tab, "Options")
    def save_config(self):
        new_config = {
            "printer_name": self.printer_combo.currentText(),
            "paper_width": self.paper_width.currentText(),
            "font_size": self.font_size.currentText(),
            "header_text": self.header_text.text(),
            "shop_name": self.shop_name.text(),
            "tax_id": self.tax_id.text(),
            "footer_text": self.footer_text.toPlainText(),
            "show_savings": self.show_savings.isChecked(),
            "show_mrp": self.show_mrp.isChecked()
        }
        if self.printer_manager.save_config(new_config):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not save printer configuration.")
    def closeEvent(self, event):
        if self.hide_cancel:
            event.ignore()
        else:
            super().closeEvent(event)
