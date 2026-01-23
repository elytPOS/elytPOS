import copy
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFormLayout,
    QComboBox,
    QPushButton,
    QMessageBox,
    QTabWidget,
    QWidget,
    QLineEdit,
    QTextEdit,
    QCheckBox,
    QHBoxLayout,
    QTextBrowser,
    QFrame,
    QSpinBox,
    QInputDialog,
    QGroupBox,
    QFontComboBox,
    QDoubleSpinBox,
    QScrollArea,
)
from PySide6.QtCore import Qt


class PrinterConfigDialog(QDialog):
    def __init__(self, printer_manager, parent=None, hide_cancel=False):
        super().__init__(parent)
        self.setWindowTitle("Printer Configuration")
        self.hide_cancel = hide_cancel
        if hide_cancel:
            self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self.printer_manager = printer_manager
        # Work on a copy to allow "Cancel" to work properly
        self.full_config = copy.deepcopy(self.printer_manager.full_config)
        self.active_layout_name = self.full_config["active_layout"]
        self.config = self.full_config["layouts"][self.active_layout_name]

        self.updating_ui = True

        # Main Layout
        main_layout = QHBoxLayout(self)

        # Left Panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Receipt Designer")
        title.setObjectName("title")
        left_layout.addWidget(title, 0, Qt.AlignCenter)

        self.tabs = QTabWidget()
        self.setup_general_tab()
        self.setup_page_tab()
        self.setup_typography_tab()
        self.setup_business_tab()
        self.setup_labels_tab()
        self.setup_options_tab()
        left_layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        if hide_cancel:
            self.cancel_btn.hide()

        save_btn = QPushButton("Save All Settings")
        save_btn.setObjectName("btnSave")
        save_btn.clicked.connect(self.save_and_exit)
        btn_layout.addWidget(save_btn)
        left_layout.addLayout(btn_layout)

        main_layout.addWidget(left_panel, 1)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Right Panel: Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("Live Paper Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(preview_label, 0, Qt.AlignCenter)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setAlignment(Qt.AlignCenter)
        self.preview_scroll.setObjectName("previewScroll")

        self.paper_widget = QWidget()
        self.paper_layout = QVBoxLayout(self.paper_widget)
        self.paper_layout.setContentsMargins(0, 0, 0, 0)

        self.preview_area = QTextBrowser()
        self.preview_area.setOpenExternalLinks(False)
        # Paper-like styling: white with shadow
        self.preview_area.setStyleSheet(
            "background-color: white; color: black; border: 1px solid #000;"
        )
        self.paper_layout.addWidget(self.preview_area)
        self.preview_scroll.setWidget(self.paper_widget)

        right_layout.addWidget(self.preview_scroll)
        main_layout.addWidget(right_panel, 1)

        self.setFixedWidth(1100)
        self.setFixedHeight(700)

        self.updating_ui = False
        self.update_preview()

    def setup_general_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        # Layout Management
        layout_box = QGroupBox("Active Layout")
        l_layout = QVBoxLayout(layout_box)

        self.layout_combo = QComboBox()
        self.layout_combo.addItems(list(self.full_config["layouts"].keys()))
        self.layout_combo.setCurrentText(self.active_layout_name)
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        l_layout.addWidget(self.layout_combo)

        btn_row = QHBoxLayout()
        btn_new = QPushButton("New")
        btn_new.clicked.connect(self.new_layout)
        btn_del = QPushButton("Delete")
        btn_del.setObjectName("btnDelete")
        btn_del.clicked.connect(self.delete_layout)
        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_del)
        l_layout.addLayout(btn_row)

        form.addRow(layout_box)

        # Printer Selection
        self.printer_combo = QComboBox()
        self.available_printers = self.printer_manager.get_available_printers()
        self.printer_combo.addItems(self.available_printers)
        if self.config.get("printer_name") in self.available_printers:
            self.printer_combo.setCurrentText(self.config["printer_name"])
        self.printer_combo.currentTextChanged.connect(self.on_ui_change)
        form.addRow("Target Printer:", self.printer_combo)

        # Bill Theme
        self.bill_theme = QComboBox()
        self.bill_theme.addItems(["Classic", "Modern", "Minimal"])
        self.bill_theme.setCurrentText(self.config.get("bill_theme", "Classic"))
        self.bill_theme.currentTextChanged.connect(self.on_ui_change)
        form.addRow("Visual Theme:", self.bill_theme)

        self.tabs.addTab(tab, "General")

    def setup_page_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.presets = QComboBox()
        self.presets.addItems(
            ["Custom", "Thermal 58mm", "Thermal 76mm", "Thermal 80mm", "A4", "A5"]
        )
        self.presets.currentTextChanged.connect(self.apply_preset)
        form.addRow("Quick Presets:", self.presets)

        self.paper_width_mm = QDoubleSpinBox()
        self.paper_width_mm.setRange(20, 300)
        self.paper_width_mm.setValue(self.config.get("paper_width_mm", 76.2))
        self.paper_width_mm.setSuffix(" mm")
        self.paper_width_mm.valueChanged.connect(self.on_ui_change)
        form.addRow("Paper Width:", self.paper_width_mm)

        self.paper_height_mm = QDoubleSpinBox()
        self.paper_height_mm.setRange(50, 2000)
        self.paper_height_mm.setValue(self.config.get("paper_height_mm", 300))
        self.paper_height_mm.setSuffix(" mm")
        self.paper_height_mm.valueChanged.connect(self.on_ui_change)
        form.addRow("Max Paper Height:", self.paper_height_mm)

        # Margins
        margin_box = QGroupBox("Margins (mm)")
        m_form = QFormLayout(margin_box)
        self.m_left = QDoubleSpinBox()
        self.m_right = QDoubleSpinBox()
        self.m_top = QDoubleSpinBox()
        self.m_bottom = QDoubleSpinBox()
        for w in [self.m_left, self.m_right, self.m_top, self.m_bottom]:
            w.setRange(0, 50)
            w.valueChanged.connect(self.on_ui_change)

        self.m_left.setValue(self.config.get("margin_left", 1.0))
        self.m_right.setValue(self.config.get("margin_right", 1.0))
        self.m_top.setValue(self.config.get("margin_top", 1.0))
        self.m_bottom.setValue(self.config.get("margin_bottom", 1.0))

        m_form.addRow("Left:", self.m_left)
        m_form.addRow("Right:", self.m_right)
        m_form.addRow("Top:", self.m_top)
        m_form.addRow("Bottom:", self.m_bottom)
        form.addRow(margin_box)

        self.tabs.addTab(tab, "Page Layout")

    def setup_typography_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setCurrentFont(
            self.config.get("font_family", "FiraCode Nerd Font")
        )
        self.font_family_combo.currentFontChanged.connect(self.on_ui_change)
        form.addRow("Font Family:", self.font_family_combo)

        self.font_size_preset = QComboBox()
        self.font_size_preset.addItems(["Small", "Medium", "Large"])
        self.font_size_preset.setCurrentText(self.config.get("font_size", "Medium"))
        self.font_size_preset.currentTextChanged.connect(self.on_ui_change)
        form.addRow("Font Size (Base):", self.font_size_preset)

        self.tabs.addTab(tab, "Typography")

    def setup_business_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.shop_name = QLineEdit(self.config.get("shop_name", "KIRANA STORE"))
        self.header_text = QLineEdit(self.config.get("header_text", "ELYT POS"))
        self.tax_id = QLineEdit(self.config.get("tax_id", ""))
        self.footer_text = QTextEdit()
        self.footer_text.setPlainText(
            self.config.get("footer_text", "Thank you!").replace("<br/>", "\n")
        )
        self.footer_text.setFixedHeight(80)

        for w in [self.shop_name, self.header_text, self.tax_id]:
            w.textChanged.connect(self.on_ui_change)
        self.footer_text.textChanged.connect(self.on_ui_change)

        form.addRow("Shop Name:", self.shop_name)
        form.addRow("Header Title:", self.header_text)
        form.addRow("GST/Tax ID:", self.tax_id)
        form.addRow("Footer Text:", self.footer_text)

        self.tabs.addTab(tab, "Business Info")

    def setup_labels_tab(self):
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)

        self.label_bill_to = QLineEdit(self.config.get("label_bill_to", "Bill To:"))
        self.label_gst = QLineEdit(self.config.get("label_gst", "GST:"))
        self.label_date = QLineEdit(self.config.get("label_date", "Date:"))
        self.label_bill_no = QLineEdit(self.config.get("label_bill_no", "Bill:"))
        self.label_item_col = QLineEdit(
            self.config.get("label_item_col", "Item Description")
        )
        self.label_amount_col = QLineEdit(self.config.get("label_amount_col", "Amount"))
        self.label_net_payable = QLineEdit(
            self.config.get("label_net_payable", "NET PAYABLE:")
        )
        self.label_total_savings = QLineEdit(
            self.config.get("label_total_savings", "Total Savings:")
        )
        self.currency_symbol = QLineEdit(self.config.get("currency_symbol", "₹"))

        self.item_col_width = QSpinBox()
        self.item_col_width.setRange(20, 90)
        self.item_col_width.setValue(self.config.get("item_col_width", 70))
        self.item_col_width.setSuffix("%")

        fields = [
            self.label_bill_to,
            self.label_gst,
            self.label_date,
            self.label_bill_no,
            self.label_item_col,
            self.label_amount_col,
            self.label_net_payable,
            self.label_total_savings,
            self.currency_symbol,
        ]
        for f in fields:
            f.textChanged.connect(self.on_ui_change)
        self.item_col_width.valueChanged.connect(self.on_ui_change)

        form.addRow("Label 'Bill To':", self.label_bill_to)
        form.addRow("Label 'GST':", self.label_gst)
        form.addRow("Label 'Date':", self.label_date)
        form.addRow("Label 'Bill No':", self.label_bill_no)
        form.addRow("Col 'Item':", self.label_item_col)
        form.addRow("Col 'Amount':", self.label_amount_col)
        form.addRow("Label 'Net Payable':", self.label_net_payable)
        form.addRow("Label 'Savings':", self.label_total_savings)
        form.addRow("Currency:", self.currency_symbol)
        form.addRow("Item Col Width:", self.item_col_width)

        scroll.setWidget(content)
        vbox = QVBoxLayout(tab)
        vbox.addWidget(scroll)
        self.tabs.addTab(tab, "Labels")

    def setup_options_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.show_savings = QCheckBox("Show 'Total Savings' on Receipt")
        self.show_savings.setChecked(self.config.get("show_savings", True))
        self.show_mrp = QCheckBox("Show MRP for Items")
        self.show_mrp.setChecked(self.config.get("show_mrp", True))

        self.show_savings.stateChanged.connect(self.on_ui_change)
        self.show_mrp.stateChanged.connect(self.on_ui_change)

        layout.addWidget(self.show_savings)
        layout.addWidget(self.show_mrp)
        layout.addStretch()
        self.tabs.addTab(tab, "Options")

    def on_ui_change(self):
        if self.updating_ui:
            return
        # Update current layout dictionary from UI
        self.sync_config_from_ui()
        self.update_preview()

    def sync_config_from_ui(self):
        c = self.config
        c["printer_name"] = self.printer_combo.currentText()
        c["bill_theme"] = self.bill_theme.currentText()
        c["paper_width_mm"] = self.paper_width_mm.value()
        c["paper_height_mm"] = self.paper_height_mm.value()
        c["margin_left"] = self.m_left.value()
        c["margin_right"] = self.m_right.value()
        c["margin_top"] = self.m_top.value()
        c["margin_bottom"] = self.m_bottom.value()
        c["font_family"] = self.font_family_combo.currentText()
        c["font_size"] = self.font_size_preset.currentText()
        c["shop_name"] = self.shop_name.text()
        c["header_text"] = self.header_text.text()
        c["tax_id"] = self.tax_id.text()
        c["footer_text"] = self.footer_text.toPlainText()
        c["label_bill_to"] = self.label_bill_to.text()
        c["label_gst"] = self.label_gst.text()
        c["label_date"] = self.label_date.text()
        c["label_bill_no"] = self.label_bill_no.text()
        c["label_item_col"] = self.label_item_col.text()
        c["label_amount_col"] = self.label_amount_col.text()
        c["label_net_payable"] = self.label_net_payable.text()
        c["label_total_savings"] = self.label_total_savings.text()
        c["currency_symbol"] = self.currency_symbol.text()
        c["item_col_width"] = self.item_col_width.value()
        c["show_savings"] = self.show_savings.isChecked()
        c["show_mrp"] = self.show_mrp.isChecked()

    def refresh_ui(self):
        self.updating_ui = True
        c = self.config

        self.bill_theme.setCurrentText(c.get("bill_theme", "Classic"))
        if c.get("printer_name") in self.available_printers:
            self.printer_combo.setCurrentText(c["printer_name"])

        self.paper_width_mm.setValue(c.get("paper_width_mm", 76.2))
        self.paper_height_mm.setValue(c.get("paper_height_mm", 300))
        self.m_left.setValue(c.get("margin_left", 1.0))
        self.m_right.setValue(c.get("margin_right", 1.0))
        self.m_top.setValue(c.get("margin_top", 1.0))
        self.m_bottom.setValue(c.get("margin_bottom", 1.0))

        self.font_family_combo.setCurrentText(
            c.get("font_family", "FiraCode Nerd Font")
        )
        self.font_size_preset.setCurrentText(c.get("font_size", "Medium"))

        self.shop_name.setText(c.get("shop_name", ""))
        self.header_text.setText(c.get("header_text", ""))
        self.tax_id.setText(c.get("tax_id", ""))
        self.footer_text.setPlainText(c.get("footer_text", "").replace("<br/>", "\n"))

        self.label_bill_to.setText(c.get("label_bill_to", "Bill To:"))
        self.label_gst.setText(c.get("label_gst", "GST:"))
        self.label_date.setText(c.get("label_date", "Date:"))
        self.label_bill_no.setText(c.get("label_bill_no", "Bill:"))
        self.label_item_col.setText(c.get("label_item_col", "Item Description"))
        self.label_amount_col.setText(c.get("label_amount_col", "Amount"))
        self.label_net_payable.setText(c.get("label_net_payable", "NET PAYABLE:"))
        self.label_total_savings.setText(c.get("label_total_savings", "Total Savings:"))
        self.currency_symbol.setText(c.get("currency_symbol", "₹"))
        self.item_col_width.setValue(c.get("item_col_width", 70))

        self.show_savings.setChecked(c.get("show_savings", True))
        self.show_mrp.setChecked(c.get("show_mrp", True))

        self.updating_ui = False
        self.update_preview()

    def change_layout(self, name):
        if not name or self.updating_ui:
            return
        self.sync_config_from_ui()  # Save current UI state to the old layout dict first
        self.active_layout_name = name
        self.full_config["active_layout"] = name
        self.config = self.full_config["layouts"][name]
        self.refresh_ui()

    def new_layout(self):
        name, ok = QInputDialog.getText(self, "New Layout", "Enter layout name:")
        if ok and name:
            if name in self.full_config["layouts"]:
                QMessageBox.warning(self, "Error", "Name already exists.")
                return
            # Clone current config
            self.sync_config_from_ui()
            self.full_config["layouts"][name] = copy.deepcopy(self.config)
            self.layout_combo.addItem(name)
            self.layout_combo.setCurrentText(name)

    def delete_layout(self):
        name = self.layout_combo.currentText()
        if name == "Default":
            QMessageBox.warning(self, "Error", "Cannot delete Default.")
            return
        if QMessageBox.question(self, "Delete", f"Delete '{name}'?") == QMessageBox.Yes:
            del self.full_config["layouts"][name]
            self.updating_ui = True
            self.layout_combo.removeItem(self.layout_combo.currentIndex())
            self.updating_ui = False
            self.change_layout(self.layout_combo.currentText())

    def apply_preset(self, preset):
        if preset == "Custom" or self.updating_ui:
            return
        self.updating_ui = True
        if preset == "Thermal 58mm":
            self.paper_width_mm.setValue(58.0)
        elif preset == "Thermal 76mm":
            self.paper_width_mm.setValue(76.2)
        elif preset == "Thermal 80mm":
            self.paper_width_mm.setValue(80.0)
        elif preset == "A4":
            self.paper_width_mm.setValue(210.0)
            self.paper_height_mm.setValue(297.0)
        elif preset == "A5":
            self.paper_width_mm.setValue(148.0)
            self.paper_height_mm.setValue(210.0)
        self.updating_ui = False
        self.on_ui_change()

    def update_preview(self):
        # Scale mm to pixels for preview (roughly 3.78px per mm)
        px_width = int(self.paper_width_mm.value() * 3.78)
        self.preview_area.setFixedWidth(px_width)

        dummy_items = [
            {"name": "Milk", "quantity": 2, "price": 30.00, "mrp": 32.00, "uom": "pkt"},
            {
                "name": "Bread",
                "quantity": 1,
                "price": 45.00,
                "mrp": 50.00,
                "uom": "loaf",
            },
            {
                "name": "Rice (Basmati)",
                "quantity": 5,
                "price": 120.00,
                "mrp": 150.00,
                "uom": "kg",
            },
        ]
        total = sum(item["quantity"] * item["price"] for item in dummy_items)
        cust_info = {"name": "Demo Customer", "mobile": "9876543210"}

        # Use current state for preview
        self.sync_config_from_ui()
        html = self.printer_manager.generate_receipt_html(
            items=dummy_items,
            total=total,
            sale_id="DEMO-101",
            customer_info=cust_info,
            config=self.config,
        )
        self.preview_area.setHtml(html)

    def save_and_exit(self):
        self.sync_config_from_ui()
        if self.printer_manager.set_full_config(self.full_config):
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save configuration.")

    def closeEvent(self, event):
        if self.hide_cancel:
            event.ignore()
        else:
            super().closeEvent(event)
