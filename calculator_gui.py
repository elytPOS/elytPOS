from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QTextEdit, 
                               QLabel, QWidget, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont
import math
import re
class CalculatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        from styles import MODERN_STYLE
        self.setStyleSheet(MODERN_STYLE)
        self.setWindowTitle("elytPOS Calculator")
        self.setMinimumSize(400, 400)
        self.allowed_names = {
            k: getattr(math, k) for k in dir(math) if not k.startswith("__")
        }
        self.allowed_names.update({
            "abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow,
        })
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFont(QFont("FiraCode Nerd Font", 10))
        self.history_display.setPlaceholderText("Calculation history...")
        layout.addWidget(self.history_display)
        self.live_result_label = QLabel("Result: 0")
        self.live_result_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14pt; padding: 5px;")
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
        help_label = QLabel("Press Enter to add to history. Result stays for chaining.")
        help_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(help_label)
        self.last_result = None
        self.input_field.setFocus()
    def showEvent(self, event):
        super().showEvent(event)
        self.input_field.setFocus()
    def eventFilter(self, obj, event):
        if obj is self.input_field and event.type() == QEvent.KeyPress:
            if self.last_result is not None and not self.input_field.text():
                text = event.text()
                if text in ('+', '-', '*', '/', '%', '^'):
                    self.input_field.setText(str(self.last_result))
        return super().eventFilter(obj, event)
    def preprocess_expression(self, expr):
        expr = expr.replace('^', '**')
        expr = expr.replace(')%', ')*0.01')
        expr = re.sub(r'(\d+(\.\d+)?)%', r'(\1*0.01)', expr)
        return expr
    def live_calculate(self):
        expr = self.input_field.text().strip()
        if not expr:
            self.live_result_label.setText(f"Result: {self.last_result if self.last_result is not None else 0}")
            return
        try:
            safe_expr = self.preprocess_expression(expr)
            result = eval(safe_expr, {"__builtins__": None}, self.allowed_names)
            if isinstance(result, (int, float)):
                if isinstance(result, float):
                    result = round(result, 8)
                self.live_result_label.setText(f"Result: {result}")
                self.live_result_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14pt; padding: 5px;")
        except Exception:
            pass
    def commit_calculation(self):
        expr = self.input_field.text().strip()
        if not expr:
            return
        try:
            safe_expr = self.preprocess_expression(expr)
            result = eval(safe_expr, {"__builtins__": None}, self.allowed_names)
            if isinstance(result, float):
                result = round(result, 8)
            self.history_display.append(f"<font color='#89b4fa'><b>calc></b></font> {expr}")
            self.history_display.append(f"<font color='#a6e3a1'><b>=</b></font> {result}\n")
            self.last_result = result
            self.input_field.setText(str(result))
            self.input_field.selectAll()
            sb = self.history_display.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception as e:
            self.history_display.append(f"<font color='#f38ba8'><b>Error:</b></font> {e}\n")
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
