import sys
import os
import psycopg2

# Add current directory to path so we can import database.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from PySide6.QtWidgets import QApplication, QDialog
from main import ConfigDialog

app = QApplication(sys.argv)

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(application_path, 'db.config')
if not os.path.exists(config_path):
    print("db.config not found. Opening Setup...")
    if ConfigDialog(config_path).exec() != QDialog.Accepted:
        print("Setup cancelled.")
        sys.exit(0)

db_manager = DatabaseManager()
conn_params = db_manager.conn_params
db_manager.close() # Release pool connections

print("Clearing database...")

try:
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cur = conn.cursor()
    
    tables = [
        "product_translations",
        "held_sale_items",
        "held_sales",
        "sale_items",
        "sales",
        "schemes",
        "product_aliases",
        "products",
        "uoms",
        "languages",
        "users"
    ]
    
    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"Dropped table {table}")
        
    cur.close()
    conn.close()
    print("All tables dropped.")
    
    print("Re-initializing database...")
    db = DatabaseManager()
    print("Database re-initialized and seeded with default values.")
    
except Exception as e:
    print(f"Error: {e}")
