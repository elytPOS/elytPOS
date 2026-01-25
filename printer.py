"Receipt printing module for elytPOS."

try:
    import cups

    CUPS_AVAILABLE = True
except ImportError:
    CUPS_AVAILABLE = False
import os
import sys
import json
from datetime import datetime
from PySide6.QtGui import QTextDocument, QFont, QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QSizeF, QMarginsF

DEFAULT_CONFIG = {
    "printer_name": None,
    "paper_width_mm": 76.2,
    "paper_height_mm": 300,
    "margin_left": 1.0,
    "margin_right": 1.0,
    "margin_top": 1.0,
    "margin_bottom": 1.0,
    "font_family": "FiraCode Nerd Font",
    "header_text": "ELYT POS",
    "shop_name": "KIRANA STORE",
    "tax_id": "",
    "footer_text": "Thank you for your visit!<br/>Items once sold cannot be returned.",
    "show_savings": True,
    "show_mrp": True,
    "font_size": "Medium",
    "label_bill_to": "Bill To:",
    "label_gst": "GST:",
    "label_date": "Date:",
    "label_bill_no": "Bill:",
    "label_item_col": "Item Description",
    "label_amount_col": "Amount",
    "label_net_payable": "NET PAYABLE:",
    "label_total_savings": "Total Savings:",
    "currency_symbol": "₹",
    "item_col_width": 70,
    "bill_theme": "Classic",
}


class ReceiptPrinter:
    def __init__(self):
        self.conn = None
        self.printers = {}
        self.config_path = self.get_config_path()
        self.full_config = {
            "active_layout": "Default",
            "layouts": {"Default": DEFAULT_CONFIG.copy()},
        }
        self.config = self.load_config()
        if CUPS_AVAILABLE:
            self.refresh_printers()

    def get_config_path(self):
        if getattr(sys, "frozen", False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, "printer_config.json")

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    saved_data = json.load(f)
                if "layouts" in saved_data and "active_layout" in saved_data:
                    self.full_config = saved_data
                else:
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(saved_data)
                    self.full_config["layouts"]["Default"] = merged
                    self.full_config["active_layout"] = "Default"
                    self.save_full_config(self.full_config)
            except Exception as e:
                print(f"Error loading printer config: {e}")

        self.config = self.get_active_config()
        return self.config

    def get_active_config(self):
        active_name = self.full_config.get("active_layout", "Default")
        return self.full_config["layouts"].get(active_name, DEFAULT_CONFIG.copy())

    def save_config(self, new_config):
        active_name = self.full_config.get("active_layout", "Default")
        if active_name not in self.full_config["layouts"]:
            self.full_config["layouts"][active_name] = {}
        self.full_config["layouts"][active_name].update(new_config)
        self.config = self.full_config["layouts"][active_name]
        return self.save_full_config(self.full_config)

    def save_full_config(self, full_data):
        try:
            with open(self.config_path, "w") as f:
                json.dump(full_data, f, indent=4)
            self.full_config = full_data
            self.config = self.get_active_config()
            return True
        except Exception as e:
            print(f"Error saving printer config: {e}")
            return False

    def get_layout_names(self):
        return list(self.full_config["layouts"].keys())

    def create_layout(self, name, base_layout_name=None):
        if name in self.full_config["layouts"]:
            return False
        base = DEFAULT_CONFIG.copy()
        if base_layout_name and base_layout_name in self.full_config["layouts"]:
            base = self.full_config["layouts"][base_layout_name].copy()
        self.full_config["layouts"][name] = base
        return self.save_full_config(self.full_config)

    def delete_layout(self, name):
        if name == "Default" or name not in self.full_config["layouts"]:
            return False
        del self.full_config["layouts"][name]
        if self.full_config["active_layout"] == name:
            self.full_config["active_layout"] = "Default"
        return self.save_full_config(self.full_config)

    def set_active_layout(self, name):
        if name not in self.full_config["layouts"]:
            return False
        self.full_config["active_layout"] = name
        return self.save_full_config(self.full_config)

    def set_full_config(self, full_data):
        """Replace the entire internal config structure and save."""
        return self.save_full_config(full_data)

    def export_layout_to_file(self, layout_name, file_path):
        """Export a specific layout configuration to a file."""
        if layout_name not in self.full_config["layouts"]:
            return False
        try:
            data = self.full_config["layouts"][layout_name].copy()
            # Store the name in the file too, for suggestion upon import
            data["_layout_name"] = layout_name
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error exporting layout: {e}")
            return False

    def import_layout_from_file(self, file_path):
        """
        Import a layout configuration from a file.
        Returns (config_dict, suggested_name) or (None, None) on failure.
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            suggested_name = data.pop("_layout_name", None)
            if not suggested_name:
                base = os.path.basename(file_path)
                suggested_name = os.path.splitext(base)[0]

            # Ensure the imported data is merged with defaults to prevent missing keys
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)

            return merged, suggested_name
        except Exception as e:
            print(f"Error importing layout: {e}")
            return None, None

    def get_configured_printer(self):
        return self.config.get("printer_name")

    def save_printer_config(self, printer_name):
        self.config["printer_name"] = printer_name
        return self.save_config(self.config)

    def refresh_printers(self):
        if not CUPS_AVAILABLE:
            return
        try:
            self.conn = cups.Connection()
            self.printers = self.conn.getPrinters()
        except Exception:
            self.printers = {}

    def get_available_printers(self):
        self.refresh_printers()
        return list(self.printers.keys())

    def _fmt(self, val):
        if float(val) == int(float(val)):
            return str(int(float(val)))
        return f"{float(val):.2f}"

    def print_receipt(
        self,
        items,
        total,
        sale_id,
        printer_name=None,
        customer_info=None,
    ):
        if not self.printers:
            self.refresh_printers()
        target = printer_name or self.config.get("printer_name")
        if not target and self.printers:
            target = list(self.printers.keys())[0]
        if not target or target not in self.printers:
            return False
        html = self.generate_receipt_html(items, total, sale_id, customer_info)
        temp_pdf = f"/tmp/receipt_{sale_id}.pdf"
        doc = QTextDocument()
        f_map = {"Small": 8, "Medium": 9, "Large": 10}
        base_size = f_map.get(self.config.get("font_size", "Medium"), 9)
        font = QFont(self.config.get("font_family", "FiraCode Nerd Font"), base_size)
        font.setBold(True)
        doc.setDefaultFont(font)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(temp_pdf)
        w_mm = float(self.config.get("paper_width_mm", 76.2))
        h_mm = float(self.config.get("paper_height_mm", 300))
        doc.setTextWidth((w_mm / 25.4) * 72 * 2.8)
        page_size = QPageSize(QSizeF(w_mm, h_mm), QPageSize.Millimeter)
        margins = QMarginsF(
            float(self.config.get("margin_left", 1)),
            float(self.config.get("margin_top", 1)),
            float(self.config.get("margin_right", 1)),
            float(self.config.get("margin_bottom", 1)),
        )
        printer.setPageLayout(
            QPageLayout(
                page_size, QPageLayout.Portrait, margins, QPageLayout.Millimeter
            )
        )
        doc.setHtml(html)
        doc.print_(printer)
        try:
            self.conn.printFile(
                target,
                temp_pdf,
                f"Bill {sale_id}",
                {
                    "page-left": "0",
                    "page-right": "0",
                    "page-top": "0",
                    "page-bottom": "0",
                },
            )
            return True
        except Exception:
            return False
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)

    def generate_receipt_html(
        self,
        items,
        total,
        sale_id,
        customer_info=None,
        config=None,
    ):
        if config is None:
            config = self.config
        theme = config.get("bill_theme", "Classic")
        if theme == "Modern":
            return self._generate_modern_html(
                items, total, sale_id, customer_info, config
            )
        if theme == "Minimal":
            return self._generate_minimal_html(
                items, total, sale_id, customer_info, config
            )
        return self._generate_classic_html(items, total, sale_id, customer_info, config)

    def _generate_classic_html(self, items, total, sale_id, customer_info, config):
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        header_text = config.get("header_text", "ELYT POS")
        shop_name = config.get("shop_name", "KIRANA STORE")
        tax_id = config.get("tax_id", "")
        footer_text = config.get("footer_text", "Thank you!").replace("\n", "<br/>")
        show_mrp = config.get("show_mrp", True)

        lbl_bill_to = config.get("label_bill_to", "Bill To:")
        lbl_gst = config.get("label_gst", "GST:")
        lbl_date = config.get("label_date", "Date:")
        lbl_bill_no = config.get("label_bill_no", "Bill:")
        lbl_item_col = config.get("label_item_col", "Item Description")
        lbl_amount_col = config.get("label_amount_col", "Amount")
        lbl_net_payable = config.get("label_net_payable", "NET PAYABLE:")
        currency = config.get("currency_symbol", "₹")
        item_col_width = config.get("item_col_width", 70)
        amount_col_width = 100 - item_col_width

        size_map = {"Small": "6pt", "Medium": "7pt", "Large": "8pt"}
        css_font_size = size_map.get(config.get("font_size", "Medium"), "7pt")
        font_family = config.get("font_family", "FiraCode Nerd Font")
        m_l = config.get("margin_left", 1)
        m_r = config.get("margin_right", 1)
        m_t = config.get("margin_top", 1)
        m_b = config.get("margin_bottom", 1)

        rows = ""
        for item in items:
            uom = item.get("uom", "")
            subtotal = item["quantity"] * item["price"]
            mrp_display = ""
            if show_mrp and item.get("mrp") and float(item.get("mrp")) > 0:
                mrp_display = f'<br/><span style="font-size:0.8em;color:#555">MRP: {self._fmt(item["mrp"])}</span>'
            rows += f"""
            <tr><td colspan="2" style="font-weight:bold">{item["name"]}</td></tr>
            <tr>
                <td style="padding-left:2mm;font-size:0.9em">{self._fmt(item["quantity"])} {uom} x {self._fmt(item["price"])} {mrp_display}</td>
                <td align="right" style="font-weight:bold">{self._fmt(subtotal)}</td>
            </tr>
            <tr><td colspan="2" style="border-bottom:0.1mm dashed #ccc;height:1px"></td></tr>
            """
        cust_html = ""
        if customer_info:
            cust_html = f'<div style="margin:2mm 0;border-bottom:0.1mm solid #ccc;padding-bottom:2mm"><b>{lbl_bill_to}</b><br/>{customer_info.get("name")}<br/>{customer_info.get("mobile")}</div>'

        tax_html = (
            f'<div style="text-align:center;font-weight:bold;margin-bottom:2mm">{lbl_gst} {tax_id}</div>'
            if tax_id
            else ""
        )

        return f"""
        <html>
        <style>
            @page {{ margin: 0; }}
            body {{ font-family: '{font_family}', monospace; padding: {m_t}mm {m_r}mm {m_b}mm {m_l}mm; font-size: {css_font_size}; color: black; }}
            .header {{ text-align: center; font-weight: 900; font-size: 1.5em; }}
            .shop {{ text-align: center; font-size: 1.2em; font-weight: bold; margin-bottom: 1mm; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ border-bottom: 0.2mm solid black; padding: 1mm 0; text-align: left; }}
            td {{ padding: 0.5mm 0; vertical-align: top; }}
        </style>
        <body>
            <div class="header">{header_text}</div>
            <div class="shop">{shop_name}</div>
            {tax_html}
            <div style="font-size:0.9em;margin-bottom:1mm;border-bottom:0.1mm solid #ccc">{lbl_date} {now} | {lbl_bill_no} #{sale_id}</div>
            {cust_html}
            <table>
                <thead><tr><th width="{item_col_width}%">{lbl_item_col}</th><th width="{amount_col_width}%" align="right">{lbl_amount_col}</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div style="border-top:0.3mm solid black;margin-top:2mm;padding-top:1mm">
                <table width="100%"><tr><td style="font-size:1.3em;font-weight:900">{lbl_net_payable}</td><td align="right" style="font-size:1.3em;font-weight:900">{currency} {self._fmt(total)}</td></tr></table>
            </div>
            <div style="text-align:center;margin-top:4mm;font-size:0.9em;border-top:0.1mm solid #ccc;padding-top:2mm">{footer_text}</div>
        </body>
        </html>
        """

    def _generate_modern_html(self, items, total, sale_id, customer_info, config):
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        shop_name = config.get("shop_name", "KIRANA STORE")
        tax_id = config.get("tax_id", "")
        footer_text = config.get("footer_text", "Thank you!").replace("\n", "<br/>")
        currency = config.get("currency_symbol", "₹")
        font_family = config.get("font_family", "sans-serif")
        size_map = {"Small": "6pt", "Medium": "7pt", "Large": "8pt"}
        css_font_size = size_map.get(config.get("font_size", "Medium"), "7pt")
        m_l = config.get("margin_left", 1)
        m_r = config.get("margin_right", 1)
        m_t = config.get("margin_top", 1)
        m_b = config.get("margin_bottom", 1)

        rows = "".join(
            [
                f'<tr style="border-bottom:0.1mm solid #eee"><td style="width:10%">{i + 1}</td><td style="width:50%;font-weight:600">{it["name"]}</td><td style="width:15%;text-align:center">{self._fmt(it["quantity"])}</td><td style="width:25%;text-align:right;font-weight:700">{self._fmt(it["quantity"] * it["price"])}</td></tr>'
                for i, it in enumerate(items)
            ]
        )

        cust_section = f'<div style="display:grid;grid-template-columns:25% 75%;font-size:0.9em;margin-bottom:2mm;padding:1mm;background:#f9f9f9"><b>Cust:</b><span>{customer_info.get("name") if customer_info else "N/A"}</span></div>'
        tax_html = (
            f'<div style="font-size:0.9em;font-weight:600;margin-top:1mm">{tax_id}</div>'
            if tax_id
            else ""
        )

        style_content = "@page { margin: 0; } "
        style_content += (
            "body { font-family: '%s', sans-serif; padding: %smm %smm %smm %smm; font-size: %s; color: #333; } "
            % (font_family, m_t, m_r, m_b, m_l, css_font_size)
        )
        style_content += ".h { text-align: center; border-bottom: 2px solid #000; padding-bottom: 2mm; margin-bottom: 2mm; } "
        style_content += (
            ".s { font-size: 1.4em; font-weight: 800; text-transform: uppercase; } "
        )
        style_content += (
            "table { width: 100%; border-collapse: collapse; margin-top: 2mm; } "
        )
        style_content += "th { border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 1mm 0; font-size: 0.9em; text-transform: uppercase; } "

        return f"""
        <html>
        <style>{style_content}</style>
        <body>
            <div class="h"><div class="s">{shop_name}</div>{tax_html}</div>
            <div style="display:grid;grid-template-columns:25% 75%;font-size:0.9em;margin-bottom:2mm"><b>Bill:</b><span>#{sale_id}</span><b>Date:</b><span>{now}</span></div>
            {cust_section}
            <table><thead><tr><th>#</th><th>Item</th><th>Qty</th><th align="right">Amt</th></tr></thead><tbody>{rows}</tbody></table>
            <div style="margin-top:4mm;border-top:2px solid #000;padding-top:2mm;display:flex;justify-content:space-between;font-size:1.3em;font-weight:900">
                <span>TOTAL</span><span>{currency} {self._fmt(total)}</span>
            </div>
            <div style="text-align:center;margin-top:6mm;font-style:italic;border-top:1px dashed #999;padding-top:2mm">{footer_text}</div>
        </body>
        </html>
        """

    def _generate_minimal_html(self, items, total, sale_id, customer_info, config):
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        shop_name = config.get("shop_name", "KIRANA STORE")
        currency = config.get("currency_symbol", "₹")
        font_family = config.get("font_family", "serif")
        size_map = {"Small": "7pt", "Medium": "8pt", "Large": "9pt"}
        css_font_size = size_map.get(config.get("font_size", "Medium"), "8pt")
        m_l = config.get("margin_left", 1)
        m_r = config.get("margin_right", 1)
        m_t = config.get("margin_top", 1)
        m_b = config.get("margin_bottom", 1)

        rows = "".join(
            [
                f'<div style="margin-bottom:3mm"><div style="display:flex;justify-content:space-between;font-weight:600"><span>{it["name"]}</span><span>{currency} {self._fmt(it["quantity"] * it["price"])}</span></div><div style="font-size:0.85em;opacity:0.8">{self._fmt(it["quantity"])} x {self._fmt(it["price"])}</div></div>'
                for it in items
            ]
        )

        style_content = "@page { margin: 0; } "
        style_content += (
            "body { font-family: '%s', serif; padding: %smm %smm %smm %smm; font-size: %s; color: #000; line-height: 1.4; } "
            % (font_family, m_t, m_r, m_b, m_l, css_font_size)
        )
        style_content += ".min-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 0.5mm solid #000; padding-bottom: 3mm; margin-bottom: 4mm; } "
        style_content += (
            ".min-shop { font-size: 1.5em; font-weight: 300; letter-spacing: 1px; } "
        )
        style_content += (
            ".min-meta { text-align: right; font-size: 0.8em; opacity: 0.7; } "
        )
        style_content += ".min-item { margin-bottom: 3mm; } "
        style_content += ".min-item-main { display: flex; justify-content: space-between; font-weight: 600; } "
        style_content += ".min-details { font-size: 0.85em; opacity: 0.8; } "
        style_content += ".min-summary { margin-top: 6mm; border-top: 0.2mm solid #ccc; padding-top: 3mm; } "
        style_content += ".min-total-row { display: flex; justify-content: space-between; font-size: 1.4em; font-weight: 200; } "
        style_content += ".min-footer { margin-top: 10mm; text-align: center; font-size: 0.8em; letter-spacing: 2px; text-transform: uppercase; opacity: 0.6; } "

        return f"""
<html>
<style>{style_content}</style>
<body>
    <div class="min-header">
        <div class="min-shop">{shop_name}</div>
        <div class="min-meta">
            INV #{sale_id}<br/>{now}
        </div>
    </div>
    <div class="min-items-list">{rows}</div>
    <div class="min-summary">
        <div class="min-total-row">
            <span>Total Amount</span>
            <span>{currency} {self._fmt(total)}</span>
        </div>
    </div>
    <div class="min-footer">~~~ {config.get("footer_text", "Thank You")} ~~~</div>
</body>
</html>
"""
