import sys
import os
import random
import configparser
import psycopg2
import crypto_utils
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta
from database import DatabaseManager
from PySide6.QtWidgets import QApplication, QDialog
from main import ConfigDialog, CompanySelectionDialog


def create_db_if_missing(config_path):
    config = configparser.ConfigParser()
    enc_path = config_path + ".enc"

    if os.path.exists(enc_path):
        try:
            content = crypto_utils.decrypt_content(enc_path)
            config.read_string(content)
        except Exception as e:
            print(f"Error reading encrypted config: {e}")
            return
    else:
        config.read(config_path)

    if "postgresql" not in config:
        return

    db_params = config["postgresql"]
    # We use a default db name for initial check if not specified in config
    dbname = db_params.get("dbname", "elytpos_db")
    user = db_params.get("user", "elytpos_user")
    password = db_params.get("password", "elytpos_password")
    host = db_params.get("host", "localhost")
    port = db_params.get("port", "5432")

    try:
        con = psycopg2.connect(
            dbname="postgres", user=user, password=password, host=host, port=port
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()

        cur.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (dbname,)
        )
        exists = cur.fetchone()

        if not exists:
            print(f"Database '{dbname}' not found. Creating...")
            cur.execute(f'CREATE DATABASE "{dbname}" OWNER "{user}"')
            print(f"Database '{dbname}' created successfully.")
        else:
            print(f"Database '{dbname}' already exists.")

        cur.close()
        con.close()
    except Exception as e:
        print(f"Warning: Could not check/create database: {e}")


def main():
    _app = QApplication(sys.argv)

    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(application_path, "db.config")
    enc_path = config_path + ".enc"

    # Ensure config exists (check both plain and enc)
    if not os.path.exists(config_path) and not os.path.exists(enc_path):
        print("db.config not found. Opening Setup...")
        if ConfigDialog(config_path).exec() != QDialog.Accepted:
            print("Setup cancelled.")
            sys.exit(0)
        # Encrypt the newly created config
        crypto_utils.encrypt_file(config_path)

    # If only config exists (no enc), encrypt it (auto-migration)
    if os.path.exists(config_path) and not os.path.exists(enc_path):
        crypto_utils.encrypt_file(config_path)

    # Load connection parameters
    config_params = DatabaseManager.load_config()

    # Use selection GUI
    sel_dlg = CompanySelectionDialog(config_params)
    if sel_dlg.exec() == QDialog.Accepted:
        selected_db = sel_dlg.selected_db
    else:
        print("Selection cancelled.")
        sys.exit(0)

    db = DatabaseManager(dbname=selected_db)
    print(f"Seeding demo data into '{selected_db}'...")

    db.add_user("admin", "admin123", "System Administrator", "admin")
    db.add_user("cashier1", "cash123", "John Cashier", "cashier")
    print("Users seeded.")

    db.add_language("Hindi", "hi")
    db.add_language("Marathi", "mr")
    langs = db.get_languages()
    hindi_id = next((lang[0] for lang in langs if lang[1] == "Hindi"), None)
    print("Languages seeded.")

    db.add_uom("gram", "g")
    db.add_uom("kilogram", "kg")
    db.add_uom("packet", "pkt")
    db.add_uom("box", "bx")
    print("UOMs seeded.")

    db.add_customer("Walk-in Customer", "0000000000")
    db.add_customer("Adnan", "9876543210", "123 Main St", "adnan@example.com")
    db.add_customer(
        "Rahul Sharma", "9988776655", "456 Park Avenue", "rahul@example.com"
    )
    customers = db.get_customers()
    print("Customers seeded.")

    products_data = [
        (
            "Amul Butter 100g",
            "8901234001",
            60.0,
            55.0,
            "Dairy",
            "pcs",
            "AMUL100,BUTTER100",
            50.0,
            100,
        ),
        (
            "Tata Salt 1kg",
            "8901234002",
            28.0,
            25.0,
            "Grocery",
            "pcs",
            "SALT1KG",
            22.0,
            500,
        ),
        (
            "Maggi Noodles 70g",
            "8901234003",
            14.0,
            12.0,
            "Snacks",
            "pcs",
            "MAGGI70",
            10.5,
            2000,
        ),
        (
            "Coca Cola 500ml",
            "8901234004",
            40.0,
            35.0,
            "Beverages",
            "pcs",
            "COKE500",
            30.0,
            150,
        ),
        (
            "Basmati Rice",
            "8901234005",
            120.0,
            110.0,
            "Grocery",
            "kg",
            "RICE,BASMATI",
            95.0,
            1000,
        ),
        (
            "Washing Powder 1kg",
            "8901234006",
            150.0,
            140.0,
            "Household",
            "pcs",
            "WASH1KG",
            125.0,
            80,
        ),
        (
            "Sunlight Soap",
            "8901234007",
            30.0,
            28.0,
            "Household",
            "pcs",
            "SUNLIGHT",
            24.0,
            300,
        ),
        (
            "Pepsodent 150g",
            "8901234008",
            95.0,
            90.0,
            "Personal Care",
            "pcs",
            "PEPSO150",
            80.0,
            120,
        ),
    ]
    p_ids = []
    for name, barcode, mrp, price, cat, uom, aliases, pur, stock in products_data:
        pid = db.add_product(name, barcode, mrp, price, cat, uom, aliases, pur, stock)
        if not pid:
            res = db.find_product_by_barcode(barcode)
            if res:
                pid = res[0]
        p_ids.append(pid)

    p1, p2, p3, p4, p5, p6, p7, p8 = p_ids
    print("Products seeded.")

    if p5:
        # kg to 5kg variant
        db.add_alias(
            p5, "8901234005-5", "kg", 580.0, 540.0, 5.0, 5.0, "RICE5KG", 450.0, 50
        )

    # Add multiple MRP aliases for Maggi
    if p3:
        # Original is 14 MRP
        db.add_alias(p3, "MAGGI15", "pcs", 15.0, 13.0, 1.0, 1.0, "M15", 11.0, 100)
        db.add_alias(p3, "MAGGI16", "pcs", 16.0, 14.0, 1.0, 1.0, "M16", 11.5, 100)

    print("Aliases seeded.")

    if p1 and hindi_id:
        db.add_translation(p1, hindi_id, "अमूल मक्खन १०० ग्राम")
    if p2 and hindi_id:
        db.add_translation(p2, hindi_id, "टाटा नमक १ किलो")
    print("Translations seeded.")

    db.add_scheme(
        "Maggi Matrix Offer",
        datetime.now().date(),
        (datetime.now() + timedelta(days=30)).date(),
        [
            {
                "pid": p3,
                "mrp": 14.0,
                "min_qty": 5.0,
                "max_qty": None,
                "target_uom": "pcs",
                "benefit_type": "percent",
                "benefit_value": 10.0,
            },
            {
                "pid": p3,
                "mrp": 15.0,
                "min_qty": 1.0,
                "max_qty": None,
                "target_uom": "pcs",
                "benefit_type": "percent",
                "benefit_value": 8.0,
            },
            {
                "pid": p3,
                "mrp": 16.0,
                "min_qty": 1.0,
                "max_qty": None,
                "target_uom": "pcs",
                "benefit_type": "percent",
                "benefit_value": 5.0,
            },
        ],
    )
    print("Schemes seeded.")

    db.record_purchase(
        "Modern Wholesalers",
        "INV-001",
        [
            {"pid": p1, "qty": 50, "rate": 50.0, "uom": "pcs", "mrp": 60.0},
            {"pid": p2, "qty": 100, "rate": 22.0, "uom": "pcs", "mrp": 28.0},
        ],
        4700.0,
        timestamp=datetime.now() - timedelta(days=10),
    )
    print("Purchases seeded.")

    now = datetime.now()
    all_seeded_products = [
        (p1, "Amul Butter 100g", "8901234001", 55.0, 60.0, "pcs"),
        (p2, "Tata Salt 1kg", "8901234002", 25.0, 28.0, "pcs"),
        (p3, "Maggi Noodles 70g", "8901234003", 12.0, 14.0, "pcs"),
        (p4, "Coca Cola 500ml", "8901234004", 35.0, 40.0, "pcs"),
        (p5, "Basmati Rice", "8901234005", 110.0, 120.0, "kg"),
        (p6, "Washing Powder 1kg", "8901234006", 140.0, 150.0, "pcs"),
        (p7, "Sunlight Soap", "8901234007", 28.0, 30.0, "pcs"),
        (p8, "Pepsodent 150g", "8901234008", 90.0, 95.0, "pcs"),
    ]

    for day in range(7, -1, -1):
        date = now - timedelta(days=day)
        sales_count = random.randint(5, 15)
        for _ in range(sales_count):
            sale_time = date.replace(
                hour=random.randint(9, 21),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )

            selected = random.sample(all_seeded_products, random.randint(1, 4))
            items = []
            for pid, name, barcode, price, mrp, uom in selected:
                if not pid:
                    continue
                qty = (
                    random.randint(1, 5)
                    if uom == "pcs"
                    else round(random.uniform(0.5, 3.0), 3)
                )
                items.append(
                    {
                        "id": pid,
                        "name": name,
                        "barcode": barcode,
                        "price": price,
                        "quantity": qty,
                        "uom": uom,
                        "factor": 1.0,
                        "mrp": mrp,
                    }
                )

            if not items:
                continue
            total = sum(item["price"] * item["quantity"] for item in items)
            total = float(round(total))
            cid = random.choice(customers)[0] if customers else None
            db.process_sale(items, total, "Cash", cid, timestamp=sale_time)

    print("Sales seeded for past 7 days.")

    print("\nDemo data seeding completed successfully!")


if __name__ == "__main__":
    main()
