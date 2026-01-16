from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox, QPushButton, QMessageBox)
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
    QComboBox {
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
    QComboBox:focus {
        background-color: #45475a;
        border: 1px solid #89b4fa;
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
        
        layout = QVBoxLayout(self)
        title = QLabel("Printer Setup")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #89b4fa; margin-bottom: 10px;")
        layout.addWidget(title, 0, Qt.AlignCenter)
        
        form = QFormLayout()
        self.printer_combo = QComboBox()
        self.available_printers = self.printer_manager.get_available_printers()
        self.printer_combo.addItems(self.available_printers)
        
        # Select the currently configured printer
        current_printer = self.printer_manager.get_configured_printer()
        if current_printer in self.available_printers:
            self.printer_combo.setCurrentText(current_printer)
            
        form.addRow("Default Printer:", self.printer_combo)
        layout.addLayout(form)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("btnSave")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        
        self.setFixedWidth(400)

    def save_config(self):
        selected_printer = self.printer_combo.currentText()
        if self.printer_manager.save_printer_config(selected_printer):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not save printer configuration.")
