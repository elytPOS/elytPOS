"""
Help system for ElytPOS providing a searchable user guide and documentation.
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QTextBrowser, QPushButton, QTreeWidget, QTreeWidgetItem,
                               QSplitter, QApplication)
from PySide6.QtCore import Qt
from styles import MODERN_STYLE

class HelpDialog(QDialog):
    """
    A dialog window that displays the user guide and documentation for the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ElytPOS User Guide & Documentation")
        self.setMinimumSize(1000, 700)
        self.setWindowFlags(Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderLabel("Contents")
        self.nav_tree.setFixedWidth(250)
        self.nav_tree.itemClicked.connect(self.navigate_to_section)
        splitter.addWidget(self.nav_tree)

        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 14px;
                padding: 20px;
                border: none;
            }
        """)
        splitter.addWidget(self.content_browser)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedWidth(100)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.sections = {}
        self.nav_root = None
        self.populate_content()
        self.nav_tree.expandAll()

    def populate_content(self):
        """
        Populates the help content and navigation tree.
        """
        self.sections = {
            "intro": {
                "title": "Introduction",
                "content": """
                    <h1 style='color: #89b4fa;'>Welcome to ElytPOS</h1>
                    <p>ElytPOS is a modern, fast, and keyboard-centric Point of Sale system.
                    It emphasizes speed, ease of use, and robust inventory management.</p>
                    <p><b>Key Features:</b></p>
                    <ul>
                        <li>Fast Billing with Keyboard Shortcuts</li>
                        <li>Multi-Unit (UOM) Support (e.g., Pcs, Box, Grams)</li>
                        <li>Scheme & Offer Management</li>
                        <li>Multi-Language Printing Support</li>
                        <li>Comprehensive Sales History & Reports</li>
                    </ul>
                """
            },
            "getting_started": {
                "title": "Getting Started",
                "content": """
                    <h2 style='color: #89b4fa;'>Getting Started</h2>
                    <h3 style='color: #a6e3a1;'>1. Login</h3>
                    <p>Upon launching the application, you will be presented with the Login screen.
                    Enter your <b>Username</b> and <b>Password</b> to proceed.</p>
                    <p><i>Note: If this is the first time you are running the app, you will be prompted to create a Superuser.</i></p>
                    
                    <h3 style='color: #a6e3a1;'>2. Main Dashboard</h3>
                    <p>The main screen is the <b>Sales Entry</b> interface. This is where you will spend most of your time.
                    It is designed to be usable entirely with the keyboard.</p>
                """
            },
            "billing": {
                "title": "Billing & Sales",
                "content": """
                    <h2 style='color: #89b4fa;'>Billing & Sales Operations</h2>
                    
                    <h3 style='color: #fab387;'>Adding Items</h3>
                    <p>There are multiple ways to add items to the bill:</p>
                    <ol>
                        <li><b>Scan Barcode:</b> If you have a scanner, simply scan the product.</li>
                        <li><b>Search (F3):</b> Press <b>F3</b> to open the Product Search dialog.</li>
                        <li><b>Manual Entry:</b> Type the barcode or name directly into the grid's first column.</li>
                    </ol>
                    
                    <h3 style='color: #fab387;'>Modifying Quantities & Prices</h3>
                    <ul>
                        <li><b>Quantity:</b> Navigate to the Qty column and type the new quantity.</li>
                        <li><b>UOM:</b> You can change the Unit of Measure (e.g., from Pcs to Box).</li>
                        <li><b>MRP/Rate:</b> Select different MRPs from the dropdown if available.</li>
                    </ul>

                    <h3 style='color: #f38ba8;'>Keyboard Shortcuts (Hotkeys)</h3>
                    <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; border-color: #45475a; width: 100%;">
                        <tr style="background-color: #313244; color: #89b4fa;">
                            <th width="30%">Key</th>
                            <th>Action</th>
                        </tr>
                        <tr><td><b>F2</b></td><td>Save & Print Bill (Checkout)</td></tr>
                        <tr><td><b>F3</b></td><td>Search Product</td></tr>
                        <tr><td><b>F4</b></td><td>Clear / Reset Grid</td></tr>
                        <tr><td><b>F5</b></td><td>View Sales History / Day Book</td></tr>
                        <tr><td><b>F6</b></td><td>Hold Current Bill (Save as Draft)</td></tr>
                        <tr><td><b>F7</b></td><td>Recall Held Bill</td></tr>
                        <tr><td><b>F8</b> / Ctrl+Alt+C</td><td>Open Calculator</td></tr>
                        <tr><td><b>Esc</b></td><td>Close Window / Quit</td></tr>
                        <tr><td><b>Insert</b></td><td>Insert New Row</td></tr>
                        <tr><td><b>Delete</b></td><td>Delete Selected Row</td></tr>
                    </table>
                """
            },
            "inventory": {
                "title": "Inventory Management",
                "content": """
                    <h2 style='color: #89b4fa;'>Inventory Management</h2>
                    <p>Access via <b>Administration > Item Master</b> (Ctrl+I).</p>
                    
                    <h3 style='color: #a6e3a1;'>Adding a New Product</h3>
                    <ol>
                        <li>Fill in <b>Item Name</b> and <b>Base Barcode</b>.</li>
                        <li>Set the <b>MRP</b> and <b>Base Rate</b> (Selling Price).</li>
                        <li>Select the <b>Base UOM</b> (e.g., 'pcs').</li>
                        <li>Click <b>Save Base Item (F2)</b>.</li>
                    </ol>
                    
                    <h3 style='color: #fab387;'>Alternate Units (Aliases)</h3>
                    <p>Powerful feature for selling in different pack sizes.</p>
                    <ul>
                        <li><b>Base Item:</b> Coke Bottle (UOM: pcs)</li>
                        <li><b>Alias:</b> Coke Case (UOM: Case)</li>
                        <li><b>Factor:</b> How many base items in the alias? (e.g., 24).</li>
                    </ul>
                """
            },
            "admin": {
                "title": "Administration",
                "content": """
                    <h2 style='color: #89b4fa;'>Administration & Maintenance</h2>
                    
                    <h3 style='color: #a6e3a1;'>User Management</h3>
                    <p><b>User Master:</b> Create accounts for Staff, Managers, or Admins.</p>
                    <ul>
                        <li><b>Admin:</b> Full access to all features.</li>
                        <li><b>Manager:</b> Access to inventory but restricted from maintenance.</li>
                        <li><b>Staff:</b> Sales entry only.</li>
                    </ul>

                    <h3 style='color: #a6e3a1;'>Maintenance</h3>
                    <p><b>Backup Database:</b> Always take regular backups via <i>Administration > Maintenance</i>.</p>
                    <p><b>Recycle Bin:</b> Deleted items stay here for 30 days before permanent removal.</p>

                    <h3 style='color: #a6e3a1;'>Printing</h3>
                    <p>Configure your thermal printer in <b>Administration > Printer Settings</b>.</p>
                """
            }
        }

        self.nav_root = QTreeWidgetItem(self.nav_tree)
        self.nav_root.setText(0, "User Guide")
        self.nav_root.setExpanded(True)

        full_html = ""

        for key, section in self.sections.items():
            item = QTreeWidgetItem(self.nav_root)
            item.setText(0, section["title"])
            item.setData(0, Qt.UserRole, key)

            full_html += f"<a name='{key}'></a>"
            full_html += f"<div style='margin-bottom: 40px;'>{section['content']}</div>"
            full_html += "<hr style='border: 1px solid #45475a;'><br>"

        self.content_browser.setHtml(full_html)

    def navigate_to_section(self, item, _column):
        """
        Navigates the content browser to the selected section.
        """
        key = item.data(0, Qt.UserRole)
        if key:
            self.content_browser.scrollToAnchor(key)

if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)

    dlg = HelpDialog()

    dlg.show()

    sys.exit(app.exec())
