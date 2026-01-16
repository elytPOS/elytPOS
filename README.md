# elytPOS

A modern, efficient Point of Sale (POS) system built with Python and Qt (PySide6).

## Features

*   **Fast Billing:** Optimized for rapid keyboard-only entry.
*   **Inventory Management:** Track stock, manage products, and handle barcodes.
*   **Customer Management:** Maintain a customer database for quick lookups and history.
*   **Scheme/Discount Management:** Flexible promotional schemes (BOGO, percentage off, etc.).
*   **Multi-User & Security:** Role-based access control with a Superuser.
*   **Modern UI:** Clean, dark-themed interface designed for ergonomics.
*   **Robust Database:** Powered by PostgreSQL for reliability and data integrity.
*   **Printing:** Direct thermal receipt printing support.

## Installation

1.  Ensure you have Python 3.10+ and PostgreSQL installed.
2.  Clone the repository.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure your database connection in `db.config` (created on first run).

## Usage

Run the application:
```bash
python main.py
```

## Shortcuts

*   **F2:** Save / Checkout
*   **F3:** Product Search / Item Lookup
*   **F4:** Clear Grid
*   **F5:** Sales History
*   **F6:** Hold Bill
*   **F7:** Recall Held Bill
*   **Esc:** Close Window / Quit

## License

© 2026 Mohammed Adnan. All rights reserved.
