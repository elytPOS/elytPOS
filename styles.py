"""
Appearance themes and styling for elytPOS.
"""

import os
import sys


def get_app_path():
    """
    Get the base path of the application, handling both dev and PyInstaller environments.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


THEMES = {
    "mocha": {
        "bg": "#1e1e2e",
        "fg": "#ffffff",
        "accent": "#89b4fa",
        "input_bg": "#313244",
        "border": "#45475a",
        "header_bg": "#313244",
        "header_fg": "#89b4fa",
        "selection_bg": "#313244",
        "alternate_bg": "#1e1e2e",
        "hover": "#45475a",
        "table_bg": "#181825",
        "danger": "#f38ba8",
        "success": "#a6e3a1",
        "warning": "#fab387",
        "btn_fg": "#1e1e2e",
    },
    "latte": {
        "bg": "#eff1f5",
        "fg": "#4c4f69",
        "accent": "#1e66f5",
        "input_bg": "#ccd0da",
        "border": "#bcc0cc",
        "header_bg": "#ccd0da",
        "header_fg": "#1e66f5",
        "selection_bg": "#ccd0da",
        "alternate_bg": "#eff1f5",
        "hover": "#bcc0cc",
        "table_bg": "#e6e9ef",
        "danger": "#d20f39",
        "success": "#40a02b",
        "warning": "#df8e1d",
        "btn_fg": "#eff1f5",
    },
    "nord": {
        "bg": "#2e3440",
        "fg": "#eceff4",
        "accent": "#88c0d0",
        "input_bg": "#3b4252",
        "border": "#4c566a",
        "header_bg": "#3b4252",
        "header_fg": "#88c0d0",
        "selection_bg": "#434c5e",
        "alternate_bg": "#2e3440",
        "hover": "#4c566a",
        "table_bg": "#242933",
        "danger": "#bf616a",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "btn_fg": "#2e3440",
    },
    "dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "accent": "#bd93f9",
        "input_bg": "#44475a",
        "border": "#6272a4",
        "header_bg": "#44475a",
        "header_fg": "#bd93f9",
        "selection_bg": "#44475a",
        "alternate_bg": "#282a36",
        "hover": "#6272a4",
        "table_bg": "#1e1f29",
        "danger": "#ff5555",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "btn_fg": "#282a36",
    },
    "amoled": {
        "bg": "#000000",
        "fg": "#ffffff",
        "accent": "#bb86fc",
        "input_bg": "#121212",
        "border": "#333333",
        "header_bg": "#121212",
        "header_fg": "#bb86fc",
        "selection_bg": "#333333",
        "alternate_bg": "#000000",
        "hover": "#333333",
        "table_bg": "#000000",
        "danger": "#cf6679",
        "success": "#03dac6",
        "warning": "#ffb74d",
        "btn_fg": "#000000",
    },
    "emerald": {
        "bg": "#06201b",
        "fg": "#d1fae5",
        "accent": "#10b981",
        "input_bg": "#064e3b",
        "border": "#065f46",
        "header_bg": "#064e3b",
        "header_fg": "#10b981",
        "selection_bg": "#065f46",
        "alternate_bg": "#06201b",
        "hover": "#065f46",
        "table_bg": "#022c22",
        "danger": "#ef4444",
        "success": "#34d399",
        "warning": "#f59e0b",
        "btn_fg": "#06201b",
    },
    "tokyo_night": {
        "bg": "#1a1b26",
        "fg": "#c0caf5",
        "accent": "#7aa2f7",
        "input_bg": "#24283b",
        "border": "#414868",
        "header_bg": "#24283b",
        "header_fg": "#7aa2f7",
        "selection_bg": "#33467c",
        "alternate_bg": "#1a1b26",
        "hover": "#414868",
        "table_bg": "#16161e",
        "danger": "#f7768e",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "btn_fg": "#1a1b26",
    },
    "gruvbox": {
        "bg": "#282828",
        "fg": "#ebdbb2",
        "accent": "#83a598",
        "input_bg": "#3c3836",
        "border": "#504945",
        "header_bg": "#3c3836",
        "header_fg": "#83a598",
        "selection_bg": "#504945",
        "alternate_bg": "#282828",
        "hover": "#665c54",
        "table_bg": "#1d2021",
        "danger": "#fb4934",
        "success": "#b8bb26",
        "warning": "#fabd2f",
        "btn_fg": "#282828",
    },
    "one_dark": {
        "bg": "#282c34",
        "fg": "#abb2bf",
        "accent": "#61afef",
        "input_bg": "#3e4451",
        "border": "#4b5263",
        "header_bg": "#3e4451",
        "header_fg": "#61afef",
        "selection_bg": "#4b5263",
        "alternate_bg": "#282c34",
        "hover": "#5c6370",
        "table_bg": "#21252b",
        "danger": "#e06c75",
        "success": "#98c379",
        "warning": "#d19a66",
        "btn_fg": "#282c34",
    },
    "rose_pine": {
        "bg": "#191724",
        "fg": "#e0def4",
        "accent": "#ebbcba",
        "input_bg": "#26233a",
        "border": "#403d52",
        "header_bg": "#26233a",
        "header_fg": "#ebbcba",
        "selection_bg": "#403d52",
        "alternate_bg": "#191724",
        "hover": "#524f67",
        "table_bg": "#1f1d2e",
        "danger": "#eb6f92",
        "success": "#9ccfd8",
        "warning": "#f6c177",
        "btn_fg": "#191724",
    },
    "solarized_dark": {
        "bg": "#002b36",
        "fg": "#839496",
        "accent": "#268bd2",
        "input_bg": "#073642",
        "border": "#586e75",
        "header_bg": "#073642",
        "header_fg": "#268bd2",
        "selection_bg": "#586e75",
        "alternate_bg": "#002b36",
        "hover": "#657b83",
        "table_bg": "#00212b",
        "danger": "#dc322f",
        "success": "#859900",
        "warning": "#b58900",
        "btn_fg": "#002b36",
    },
    "everforest": {
        "bg": "#2d353b",
        "fg": "#d3c6aa",
        "accent": "#a7c080",
        "input_bg": "#343f44",
        "border": "#3d484d",
        "header_bg": "#343f44",
        "header_fg": "#a7c080",
        "selection_bg": "#3d484d",
        "alternate_bg": "#2d353b",
        "hover": "#475258",
        "table_bg": "#232a2e",
        "danger": "#e67e80",
        "success": "#a7c080",
        "warning": "#dbbc7f",
        "btn_fg": "#2d353b",
    },
    "frappe": {
        "bg": "#303446",
        "fg": "#c6d0f5",
        "accent": "#8caaee",
        "input_bg": "#414559",
        "border": "#51576d",
        "header_bg": "#414559",
        "header_fg": "#8caaee",
        "selection_bg": "#51576d",
        "alternate_bg": "#303446",
        "hover": "#626880",
        "table_bg": "#292c3c",
        "danger": "#e78284",
        "success": "#a6d189",
        "warning": "#ef9f76",
        "btn_fg": "#303446",
    },
    "monokai": {
        "bg": "#272822",
        "fg": "#f8f8f2",
        "accent": "#a6e22e",
        "input_bg": "#3e3d32",
        "border": "#49483e",
        "header_bg": "#3e3d32",
        "header_fg": "#a6e22e",
        "selection_bg": "#49483e",
        "alternate_bg": "#272822",
        "hover": "#75715e",
        "table_bg": "#1e1f1c",
        "danger": "#f92672",
        "success": "#a6e22e",
        "warning": "#fd971f",
        "btn_fg": "#272822",
    },
    "synthwave84": {
        "bg": "#262335",
        "fg": "#ffffff",
        "accent": "#ff7edb",
        "input_bg": "#241b30",
        "border": "#443551",
        "header_bg": "#241b30",
        "header_fg": "#ff7edb",
        "selection_bg": "#443551",
        "alternate_bg": "#262335",
        "hover": "#34294f",
        "table_bg": "#1a1a2a",
        "danger": "#fe4450",
        "success": "#72f1b8",
        "warning": "#fede5d",
        "btn_fg": "#262335",
    },
    "night_owl": {
        "bg": "#011627",
        "fg": "#d6deeb",
        "accent": "#82aaff",
        "input_bg": "#0b2942",
        "border": "#1d3b53",
        "header_bg": "#0b2942",
        "header_fg": "#82aaff",
        "selection_bg": "#1d3b53",
        "alternate_bg": "#011627",
        "hover": "#2d4f67",
        "table_bg": "#011121",
        "danger": "#ef5350",
        "success": "#22da6e",
        "warning": "#ffcb8b",
        "btn_fg": "#011627",
    },
}


def get_style(theme_name="mocha"):
    """
    Generate QSS stylesheet for the given theme.
    """
    t = THEMES.get(theme_name, THEMES["mocha"])
    return f"""
    QWidget {{
        background-color: {t["bg"]};
        color: {t["fg"]};
    }}
    QMainWindow, QDialog {{
        background-color: {t["bg"]};
        color: {t["fg"]};
    }}
    QGroupBox {{
        border: 1px solid {t["border"]};
        margin-top: 10px;
        font-weight: bold;
        color: {t["accent"]};
        border-radius: 6px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        background-color: {t["bg"]};
    }}
    QLabel {{
        color: {t["fg"]};
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
    }}
    QLabel#title {{
        font-size: 20pt;
        font-weight: bold;
        color: {t["accent"]};
        margin-bottom: 10px;
    }}
    QLabel#info {{
        color: {t["warning"]};
        margin-bottom: 15px;
    }}
    QLabel#total-label {{
        font-size: 24pt;
        font-weight: bold;
        color: {t["accent"]};
    }}
    QLabel#danger {{
        color: {t["danger"]};
        font-weight: bold;
    }}
    QLabel#copyright {{
        font-size: 9pt;
        color: {t["fg"]};
        margin-top: 15px;
        opacity: 0.7;
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QAbstractSpinBox, QComboBox, QTextEdit {{
        background-color: {t["input_bg"]};
        border: 1px solid {t["border"]};
        padding: 6px;
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
        color: {t["fg"]};
        selection-background-color: {t["accent"]};
        selection-color: {t["bg"]};
        border-radius: 4px;
    }}
    QComboBox:focus, QLineEdit:focus, QDoubleSpinBox:focus,
    QAbstractSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
        background-color: {t["hover"]};
        border: 1px solid {t["accent"]};
    }}
    QComboBox#grid-combo {{
        background-color: transparent;
        border: none;
        padding: 0px;
    }}
    QMenuBar {{
        background-color: {t["bg"]};
        color: {t["fg"]};
        border-bottom: 1px solid {t["border"]};
    }}
    QMenuBar::item {{
        background-color: {t["bg"]};
        color: {t["fg"]};
        padding: 8px 12px;
    }}
    QMenuBar::item:selected {{
        background-color: {t["input_bg"]};
    }}
    QMenu {{
        background-color: {t["bg"]};
        color: {t["fg"]};
        border: 1px solid {t["border"]};
    }}
    QMenu::item:selected {{
        background-color: {t["input_bg"]};
    }}

    QTableWidget {{
        background-color: {t["table_bg"]};
        gridline-color: {t["input_bg"]};
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
        color: {t["fg"]};
        selection-background-color: {t["selection_bg"]};
        alternate-background-color: {t["alternate_bg"]};
    }}
    QHeaderView::section {{
        background-color: {t["header_bg"]};
        color: {t["header_fg"]};
        padding: 4px;
        border: 1px solid {t["border"]};
        font-weight: bold;
    }}
    QPushButton {{
        background-color: {t["input_bg"]};
        color: {t["fg"]};
        border: 1px solid {t["border"]};
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {t["hover"]};
        border: 1px solid {t["accent"]};
    }}
    QPushButton:pressed {{
        background-color: {t["accent"]};
        color: {t["btn_fg"]};
    }}
    QPushButton#btnSave, QPushButton#btnRestore {{
        background-color: {t["success"]};
        color: {t["btn_fg"]};
    }}
    QPushButton#btnSave:hover, QPushButton#btnRestore:hover {{
        opacity: 0.8;
    }}
    QPushButton#btnDelete {{
        background-color: {t["danger"]};
        color: {t["btn_fg"]};
    }}
    QScrollBar:vertical {{
        border: none;
        background: {t["table_bg"]};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {t["border"]};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    QTabWidget::pane {{
        border: 1px solid {t["border"]};
        border-radius: 4px;
        background-color: {t["bg"]};
    }}
    QTabBar::tab {{
        background-color: {t["input_bg"]};
        color: {t["fg"]};
        padding: 8px 12px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {t["accent"]};
        color: {t["btn_fg"]};
        font-weight: bold;
    }}
    QCheckBox {{
        color: {t["fg"]};
        font-family: 'FiraCode Nerd Font', monospace;
        font-size: 11pt;
        spacing: 5px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {t["border"]};
        background-color: {t["input_bg"]};
    }}
    QCheckBox::indicator:checked {{
        background-color: {t["accent"]};
        border: 1px solid {t["accent"]};
        image: url(noop); /* Removes default check if any */
    }}
    QScrollArea {{
        border: none;
        background-color: {t["bg"]};
    }}
    QScrollArea#previewScroll {{
        background-color: {t["table_bg"]};
        border: 1px solid {t["border"]};
    }}
    QFrame[frameShape="4"], QFrame[frameShape="5"] {{ /* VLine and HLine */
        color: {t["border"]};
    }}
    QListWidget {{
        background-color: {t["input_bg"]};
        border: 1px solid {t["border"]};
        color: {t["fg"]};
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {t["accent"]};
        color: {t["btn_fg"]};
    }}
    """


def get_theme_colors(theme_name="mocha"):
    """
    Get raw color dictionary for a theme.
    """
    return THEMES.get(theme_name, THEMES["mocha"])
