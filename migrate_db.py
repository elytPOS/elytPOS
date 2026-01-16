import sys
import os
import psycopg2
from database import DatabaseManager
from PySide6.QtWidgets import QApplication, QDialog
from main import ConfigDialog

def main():
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

    print("Checking for migrations...")
    try:
        # Initializing DatabaseManager automatically runs init_db() 
        # which applies all migrations defined in migrations list.
        db = DatabaseManager()
        print("Database migration check completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
