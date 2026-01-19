MODERN_STYLE = """
    QWidget {
        background-color: #1e1e2e;
        color: #ffffff;
    }
    QMainWindow, QDialog {
        background-color: #1e1e2e;
        color: #ffffff;
    }
    QGroupBox {
        border: 1px solid #45475a;
        margin-top: 10px;
        font-weight: bold;
        color: #89b4fa; /* Soft Blue */
        border-radius: 6px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        background-color: #1e1e2e;
    }
    QLabel {
        color: #ffffff;
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QAbstractSpinBox, QComboBox {
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
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QAbstractSpinBox:focus, QComboBox:focus {
        background-color: #45475a;
        border: 1px solid #89b4fa;
    }
    QMenuBar {
        background-color: #1e1e2e;
        color: #ffffff;
        border-bottom: 1px solid #45475a;
    }
    QMenuBar::item {
        background-color: #1e1e2e;
        color: #ffffff;
        padding: 8px 12px;
    }
    QMenuBar::item:selected {
        background-color: #313244;
    }
    QMenu {
        background-color: #1e1e2e;
        color: #ffffff;
        border: 1px solid #45475a;
    }
    QMenu::item:selected {
        background-color: #313244;
    }
    
    QTableWidget {
        background-color: #181825;
        gridline-color: #313244;
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
        color: #ffffff;
        selection-background-color: #313244;
        alternate-background-color: #1e1e2e;
    }
    QHeaderView::section {
        background-color: #313244;
        color: #89b4fa;
        padding: 4px;
        border: 1px solid #45475a;
        font-weight: bold;
    }
    QPushButton {
        background-color: #313244;
        color: #ffffff;
        border: 1px solid #45475a;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #45475a;
        border: 1px solid #89b4fa;
    }
    QPushButton:pressed {
        background-color: #89b4fa;
        color: #1e1e2e;
    }
    QScrollBar:vertical {
        border: none;
        background: #181825;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #45475a;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
"""
