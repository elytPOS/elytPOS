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
    "paper_width": "76mm",
    "header_text": "ELYT POS",
    "shop_name": "KIRANA STORE",
    "footer_text": "Thank you for your visit!<br/>Items once sold cannot be returned.",
    "show_savings": True,
    "show_mrp": True,
    "font_size": "Medium" # Small, Medium, Large
}

class ReceiptPrinter:
    def __init__(self):
        self.conn = None
        self.printers = {}
        self.config_path = self.get_config_path()
        self.config = self.load_config()
        
        if CUPS_AVAILABLE:
            self.refresh_printers()

    def get_config_path(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, 'printer_config.json')
    
    def get_old_config_path(self):
        # Path to the old plain text config file
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, 'printer.config')

    def load_config(self):
        config = DEFAULT_CONFIG.copy()
        
        # Check for new JSON config first
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)
            except Exception as e:
                print(f"Error loading printer config: {e}")
        
        # If no printer set, check for old config and migrate
        elif not config["printer_name"]:
            old_path = self.get_old_config_path()
            if os.path.exists(old_path):
                try:
                    with open(old_path, 'r') as f:
                        printer_name = f.read().strip()
                        if printer_name:
                            config["printer_name"] = printer_name
                            # Auto-save to new format
                            self.save_config(config)
                except Exception as e:
                    print(f"Error migrating old config: {e}")
                    
        return config

    def save_config(self, new_config):
        try:
            # Merge with existing to ensure we don't lose keys if partial update
            self.config.update(new_config)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving printer config: {e}")
            return False

    def get_configured_printer(self):
        return self.config.get("printer_name")
    
    def save_printer_config(self, printer_name):
        # Backward compatibility method called by existing dialog
        # We'll deprecate its direct use but keep it working
        self.config["printer_name"] = printer_name
        return self.save_config(self.config)

    def refresh_printers(self):
        if not CUPS_AVAILABLE:
            print("CUPS not available on this system.")
            return

        try:
            self.conn = cups.Connection()
            self.printers = self.conn.getPrinters()
        except Exception as e:
            print(f"CUPS Connection Error: {e}")
            self.printers = {}

    def get_available_printers(self):
        if not CUPS_AVAILABLE:
            return []
        self.refresh_printers()
        return list(self.printers.keys())

    def print_receipt(self, items, total, sale_id, printer_name=None, customer_info=None):
        if not self.printers:
            self.refresh_printers()
            
        if not self.printers:
            print("No printer found!")
            return False

        target_printer = printer_name if printer_name else self.config.get("printer_name")
        
        # If still no printer, try default from CUPS or first available
        if not target_printer and self.printers:
             target_printer = list(self.printers.keys())[0]

        if not target_printer or target_printer not in self.printers:
            print(f"Printer {target_printer} not found!")
            return False

        html_content = self.generate_receipt_html(items, total, sale_id, customer_info)
        
        temp_pdf = f"/tmp/receipt_{sale_id}.pdf"
        
        doc = QTextDocument()
        
        # Determine font size base
        font_size_map = {"Small": 8, "Medium": 9, "Large": 10}
        base_size = font_size_map.get(self.config.get("font_size", "Medium"), 9)
        
        font = QFont("FiraCode Nerd Font", base_size)
        font.setBold(True)
        doc.setDefaultFont(font)
        
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(temp_pdf)
        
        # Map paper width string to mm
        width_str = self.config.get("paper_width", "76mm")
        if width_str == "58mm":
            page_width_mm = 58.0
            doc_width = 160 # Approx width for 58mm
        elif width_str == "80mm":
            page_width_mm = 80.0
            doc_width = 220
        else: # 76mm default
            page_width_mm = 76.2
            doc_width = 210
            
        page_size = QPageSize(QSizeF(page_width_mm, 300), QPageSize.Millimeter)
        layout = QPageLayout(page_size, QPageLayout.Portrait, QMarginsF(1, 1, 1, 1), QPageLayout.Millimeter)
        printer.setPageLayout(layout)
        
        doc.setTextWidth(doc_width) 
        doc.setHtml(html_content)
        
        doc.print_(printer)

        try:
            self.conn.printFile(target_printer, temp_pdf, f"POS Receipt {sale_id}", {"page-left": "0", "page-right": "0", "page-top": "0", "page-bottom": "0"})
            return True
        except Exception as e:
            print(f"Printing error: {e}")
            return False
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)

    def _fmt(self, val):
        if float(val) == int(float(val)):
            return str(int(float(val)))
        return f"{float(val):.2f}"

    def generate_receipt_html(self, items, total, sale_id, customer_info=None):
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        
        # Load settings
        header_text = self.config.get("header_text", "ELYT POS")
        shop_name = self.config.get("shop_name", "KIRANA STORE")
        footer_text = self.config.get("footer_text", "Thank you!").replace("\n", "<br/>")
        show_mrp = self.config.get("show_mrp", True)
        show_savings = self.config.get("show_savings", True)
        
        # Font size adjustment for CSS
        size_map = {"Small": "6pt", "Medium": "7pt", "Large": "8pt"}
        css_font_size = size_map.get(self.config.get("font_size", "Medium"), "7pt")
        
        rows = ""
        total_mrp = 0.0
        for item in items:
            uom = item.get('uom', '')
            
            calc_rate = item['price']
            calc_mrp = item.get('mrp', 0)
            
            if uom and uom.lower() in ('g', 'gram', 'grams'):
                calc_rate /= 1000.0
                if calc_mrp: calc_mrp /= 1000.0
                
            subtotal = item['quantity'] * calc_rate
            
            total_mrp += calc_mrp * item['quantity'] if calc_mrp else subtotal
            
            mrp_display = ""
            if show_mrp and item.get('mrp') and float(item.get('mrp')) > 0:
                mrp_display = f'<br/><span class="mrp-tag">MRP: {self._fmt(item["mrp"])}</span>'

            rows += f"""
            <tr>
                <td colspan="2" class="col-name">{item['name']}</td>
            </tr>
            <tr>
                <td class="col-details">
                    {self._fmt(item['quantity'])} {uom} x {self._fmt(item['price'])}
                    {mrp_display}
                </td>
                <td class="col-amt" align="right">{self._fmt(subtotal)}</td>
            </tr>
            <tr>
                <td colspan="2" class="separator-line"></td>
            </tr>
            """

        cust_html = ""
        if customer_info:
            cust_html = f"""
            <div class="cust-section">
                <b>Bill To:</b><br/>
                {customer_info.get('name', 'N/A')}<br/>
                {customer_info.get('mobile', '')}<br/>
                {customer_info.get('address', '')}
            </div>
            """

        savings = total_mrp - total
        savings_html = ""
        if show_savings and savings > 0:
            savings_html = f"<div class='savings'>Total Savings: ₹ {self._fmt(savings)}</div>"

        html = f"""
        <html>
        <style>
            @page {{ margin: 0; }}
            body {{
                font-family: 'FiraCode Nerd Font', monospace;
                width: 100%;
                margin: 0;
                padding: 2mm;
                font-size: {css_font_size};
                color: black;
            }}
            .header {{ text-align: center; font-weight: 900; font-size: 1.5em; margin-bottom: 1mm; }}
            .shop-name {{ text-align: center; font-size: 1.2em; font-weight: bold; margin-bottom: 2mm; }}
            .info-line {{ font-size: 0.9em; margin-bottom: 1mm; border-bottom: 0.1mm solid #ccc; padding-bottom: 1mm; }}
            .cust-section {{ margin: 2mm 0; border-bottom: 0.1mm solid #ccc; padding-bottom: 2mm; font-size: 1em; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ border-bottom: 0.2mm solid black; font-size: 1em; padding: 1mm 0; text-align: left; }}
            td {{ padding: 0.5mm 0; vertical-align: top; }}
            .col-name {{ font-weight: bold; font-size: 1em; }}
            .col-details {{ font-size: 0.9em; color: #333; padding-left: 2mm; }}
            .col-amt {{ font-weight: bold; font-size: 1em; }}
            .mrp-tag {{ font-size: 0.8em; color: #555; }}
            .separator-line {{ border-bottom: 0.1mm dashed #ccc; height: 1px; }}
            .total-row {{ border-top: 0.3mm solid black; margin-top: 2mm; padding-top: 1mm; }}
            .total-table td {{ font-size: 1.3em; font-weight: 900; }}
            .savings {{ text-align: center; margin-top: 2mm; font-weight: bold; font-size: 1.1em; border: 0.2mm dashed black; padding: 1mm; }}
            .footer {{ text-align: center; margin-top: 4mm; font-size: 0.9em; border-top: 0.1mm solid #ccc; padding-top: 2mm; }}
        </style>
        <body>
            <div class="header">{header_text}</div>
            <div class="shop-name">{shop_name}</div>
            <div class="info-line">
                Date: {now} | Bill: #{sale_id}
            </div>
            
            {cust_html}

            <table>
                <thead>
                    <tr>
                        <th width="70%">Item Description</th>
                        <th width="30%" align="right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>

            <div class="total-row">
                <table class="total-table" width="100%">
                    <tr>
                        <td align="left">NET PAYABLE:</td>
                        <td align="right">₹ {self._fmt(total)}</td>
                    </tr>
                </table>
            </div>

            {savings_html}

            <div class="footer">
                {footer_text}
            </div>
        </body>
        </html>
        """
        return html
