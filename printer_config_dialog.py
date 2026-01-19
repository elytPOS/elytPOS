from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox, 
                               QPushButton, QMessageBox, QTabWidget, QWidget, QLineEdit, 
                               QTextEdit, QCheckBox, QHBoxLayout)
from PySide6.QtCore import Qt

MODERN_STYLE = """
    QWidget {
        background-color: #1e1e2e;
        color: #ffffff;
    }
    QDialog {
        background-color: #1e1e2e;
        color: #ffffff;
    }
    QLabel {
        color: #ffffff;
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
    }
    QComboBox, QLineEdit, QTextEdit {
        background-color: #313244;
        border: 1px solid #45475a;
        padding: 6px;
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
        color: #ffffff;
        selection-background-color: #89b4fa;
        selection-color: #1e1e2e;
        border-radius: 4px;
    }
    QComboBox:focus, QLineEdit:focus, QTextEdit:focus {
        background-color: #45475a;
        border: 1px solid #89b4fa;
    }
    QCheckBox {
        color: #ffffff;
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
        spacing: 5px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid #45475a;
        background-color: #313244;
    }
    QCheckBox::indicator:checked {
        background-color: #89b4fa;
        border: 1px solid #89b4fa;
        image: none; /* Add a checkmark icon if available, or rely on color */
    }
    /* Add a pseudo-element checkmark for simplicity without icon assets */
    QCheckBox::indicator:checked:after {
        content: '✔';
        color: #1e1e2e;
        position: absolute;
        top: 0px;
        left: 2px;
        font-weight: bold;
    }
    QTabWidget::pane {
        border: 1px solid #45475a;
        border-radius: 4px;
        background-color: #1e1e2e;
    }
    QTabBar::tab {
        background-color: #313244;
        color: #ffffff;
        padding: 8px 12px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background-color: #89b4fa;
        color: #1e1e2e;
        font-weight: bold;
    }
    QPushButton {
        background-color: #313244;
        border: 1px solid #45475a;
        color: #ffffff;
        padding: 8px 15px;
        font-weight: bold;
        font-family: 'FiraCode Nerd Font', monospace;
        min-width: 80px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #45475a;
        border: 1px solid #585b70;
    }
    QPushButton:pressed {
        background-color: #585b70;
    }
    QPushButton#btnSave {
        background-color: #89b4fa;
        color: #1e1e2e;
    } 
    QPushButton#btnSave:hover { background-color: #b4befe; }
"""

class PrinterConfigDialog(QDialog):
    def __init__(self, printer_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Printer Configuration")
        self.setStyleSheet(MODERN_STYLE)
        self.printer_manager = printer_manager
        self.config = self.printer_manager.load_config()
        
        layout = QVBoxLayout(self)
        title = QLabel("Printer & Receipt Setup")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #89b4fa; margin-bottom: 10px;")
        layout.addWidget(title, 0, Qt.AlignCenter)
        
        # Tabs
        self.tabs = QTabWidget()
        self.setup_printer_tab()
        self.setup_content_tab()
        self.setup_options_tab()
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
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
        
        self.footer_text = QTextEdit()
        self.footer_text.setPlainText(self.config.get("footer_text", "Thank you!").replace("<br/>", "\n"))
        self.footer_text.setFixedHeight(80)
        
        form.addRow("Header Title:", self.header_text)
        form.addRow("Shop Name:", self.shop_name)
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
            "footer_text": self.footer_text.toPlainText(),
            "show_savings": self.show_savings.isChecked(),
            "show_mrp": self.show_mrp.isChecked()
        }
        
        if self.printer_manager.save_config(new_config):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not save printer configuration.")