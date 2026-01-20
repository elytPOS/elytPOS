"""
Calculator GUI for elytPOS.
"""

import math
import re
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QTextEdit,
    QLabel,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont


class CalculatorDialog(QDialog):
    """
    A non-modal calculator dialog with history and live evaluation.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowTitle("elytPOS Calculator")
        self.setMinimumSize(400, 400)
        self.allowed_names = {
            k: getattr(math, k) for k in dir(math) if not k.startswith("__")
        }
        self.allowed_names.update(
            {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }
        )
        self.history_display = None
        self.live_result_label = None
        self.input_field = None
        self.last_result = None
        self.init_ui()

    def init_ui(self):
        """Initialize user interface components."""
        layout = QVBoxLayout(self)
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFont(QFont("FiraCode Nerd Font", 10))
        self.history_display.setPlaceholderText("Calculation history...")
        layout.addWidget(self.history_display)

        self.live_result_label = QLabel("Result: 0")
        self.live_result_label.setObjectName("total-label")
        self.live_result_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.live_result_label)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter expression (e.g., 50 * 1.18)")
        self.input_field.setFont(QFont("FiraCode Nerd Font", 12))
        self.input_field.textChanged.connect(self.live_calculate)
        self.input_field.returnPressed.connect(self.commit_calculation)
        self.input_field.installEventFilter(self)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.input_field.clear)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(clear_btn)
        layout.addLayout(input_layout)

        help_label = QLabel(
            "Press Enter to add to history. Result stays for chaining."
        )
        help_label.setObjectName("copyright")
        layout.addWidget(help_label)

        self.last_result = None
        self.input_field.setFocus()

    def showEvent(self, event):
        """Focus input field when dialog is shown."""
        super().showEvent(event)
        if self.input_field:
            self.input_field.setFocus()

    def eventFilter(self, obj, event):
        """Filter events to allow auto-filling last result on operator press."""
        if obj is self.input_field and event.type() == QEvent.KeyPress:
            if self.last_result is not None and not self.input_field.text():
                text = event.text()
                if text in ("+", "-", "*", "/", "%", "^"):
                    self.input_field.setText(str(self.last_result))
        return super().eventFilter(obj, event)

    def preprocess_expression(self, expr):
        """Convert human-friendly operators to Python ones."""
        expr = expr.replace("^", "**")
        expr = re.sub(r"(\d+(\.\d+)?)%", r"(\1*0.01)", expr)
        return expr

    def live_calculate(self):
        """Perform evaluation as user types."""
        expr = self.input_field.text().strip()
        if not expr:
            self.live_result_label.setText(
                f"Result: {self.last_result if self.last_result is not None else 0}"
            )
            return

        try:
            safe_expr = self.preprocess_expression(expr)
            result = eval(safe_expr, {"__builtins__": None}, self.allowed_names)
            if isinstance(result, (int, float)):
                if isinstance(result, float):
                    result = round(result, 8)
                self.live_result_label.setText(f"Result: {result}")
        except Exception:
            pass

    def commit_calculation(self):
        """Save calculation to history and set as last result."""
        expr = self.input_field.text().strip()
        if not expr:
            return

        try:
            safe_expr = self.preprocess_expression(expr)
            result = eval(safe_expr, {"__builtins__": None}, self.allowed_names)
            if isinstance(result, float):
                result = round(result, 8)

            self.history_display.append(
                f"<font color='#89b4fa'><b>calc></b></font> {expr}"
            )
            self.history_display.append(
                f"<font color='#a6e3a1'><b>=</b></font> {result}\n"
            )
            self.last_result = result
            self.input_field.setText(str(result))
            self.input_field.selectAll()

            sb = self.history_display.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception as e:
            self.history_display.append(
                f"<font color='#f38ba8'><b>Error:</b></font> {e}\n"
            )

    def keyPressEvent(self, event):
        """Close on escape."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
