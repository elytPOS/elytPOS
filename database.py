import psycopg2
from psycopg2 import sql
import configparser
import os
import sys

class DatabaseManager:
    def __init__(self):
        self.conn_params = self.load_config()
        self.init_db()

    def load_config(self):
        config = configparser.ConfigParser()
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(application_path, 'db.config')
        
        defaults = {
            "dbname": "elytpos_db",
            "user": "elytpos_user",
            "password": "elytpos_password",
            "host": "localhost",
            "port": "5432"
        }

        if os.path.exists(config_path):
            config.read(config_path)
            if 'postgresql' in config:
                for key in defaults:
                    if key in config['postgresql']:
                        defaults[key] = config['postgresql'][key]
        
        return defaults

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def init_db(self):
        commands = [
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                barcode VARCHAR(50) UNIQUE,
                mrp DECIMAL(12, 3) NOT NULL DEFAULT 0,
                price DECIMAL(12, 3) NOT NULL,
                category VARCHAR(100),
                base_uom VARCHAR(20) DEFAULT 'pcs',
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS product_aliases (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                barcode VARCHAR(50) UNIQUE,
                uom VARCHAR(20) NOT NULL,
                mrp DECIMAL(12, 3) NOT NULL DEFAULT 0,
                price DECIMAL(12, 3) NOT NULL,
                factor DECIMAL(12, 3) NOT NULL DEFAULT 1.0,
                qty DECIMAL(12, 3) NOT NULL DEFAULT 1.0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(12, 3) NOT NULL,
                payment_method VARCHAR(50),
                customer_id INTEGER REFERENCES customers(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sale_items (
                id SERIAL PRIMARY KEY,
                sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id),
                quantity DECIMAL(12, 3) NOT NULL,
                price_at_sale DECIMAL(12, 3) NOT NULL,
                uom VARCHAR(20),
                mrp DECIMAL(12, 3)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(12, 3) NOT NULL,
                supplier_name VARCHAR(100),
                invoice_no VARCHAR(50)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS purchase_items (
                id SERIAL PRIMARY KEY,
                purchase_id INTEGER REFERENCES purchases(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id),
                quantity DECIMAL(12, 3) NOT NULL,
                purchase_rate DECIMAL(12, 3) NOT NULL,
                uom VARCHAR(20),
                mrp DECIMAL(12, 3)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS schemes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                valid_from DATE DEFAULT CURRENT_DATE,
                valid_to DATE,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scheme_products (
                id SERIAL PRIMARY KEY,
                scheme_id INTEGER REFERENCES schemes(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                min_qty DECIMAL(12, 3) DEFAULT 0,
                max_qty DECIMAL(12, 3),
                target_uom VARCHAR(20),
                benefit_type VARCHAR(20) DEFAULT 'percent',
                benefit_value DECIMAL(12, 3) DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS uoms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(20) UNIQUE NOT NULL,
                alias VARCHAR(10) UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                is_superuser BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS held_sales (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(12, 3) NOT NULL,
                user_id INTEGER REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS held_sale_items (
                id SERIAL PRIMARY KEY,
                held_sale_id INTEGER REFERENCES held_sales(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id),
                quantity DECIMAL(12, 3) NOT NULL,
                price_at_sale DECIMAL(12, 3) NOT NULL,
                uom VARCHAR(20),
                mrp DECIMAL(12, 3)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS languages (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                code VARCHAR(10) UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                mobile VARCHAR(15) UNIQUE,
                address TEXT,
                email VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS product_translations (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                language_id INTEGER REFERENCES languages(id) ON DELETE CASCADE,
                translated_name VARCHAR(255) NOT NULL,
                UNIQUE(product_id, language_id)
            )
            """
        ]
        migrations = [
            "CREATE TABLE IF NOT EXISTS purchases (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total_amount DECIMAL(12, 3) NOT NULL, supplier_name VARCHAR(100), invoice_no VARCHAR(50));",
            "CREATE TABLE IF NOT EXISTS purchase_items (id SERIAL PRIMARY KEY, purchase_id INTEGER REFERENCES purchases(id) ON DELETE CASCADE, product_id INTEGER REFERENCES products(id), quantity DECIMAL(12, 3) NOT NULL, purchase_rate DECIMAL(12, 3) NOT NULL, uom VARCHAR(20), mrp DECIMAL(12, 3));",
            "CREATE TABLE IF NOT EXISTS customers (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, mobile VARCHAR(15) UNIQUE, address TEXT, email VARCHAR(100));",
            "ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(id);",
            "CREATE TABLE IF NOT EXISTS held_sales (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, total_amount DECIMAL(12, 3) NOT NULL, user_id INTEGER REFERENCES users(id));",
            "CREATE TABLE IF NOT EXISTS held_sale_items (id SERIAL PRIMARY KEY, held_sale_id INTEGER REFERENCES held_sales(id) ON DELETE CASCADE, product_id INTEGER REFERENCES products(id), quantity DECIMAL(12, 3) NOT NULL, price_at_sale DECIMAL(12, 3) NOT NULL, uom VARCHAR(20), mrp DECIMAL(12, 3));",
            "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL, full_name VARCHAR(100), is_superuser BOOLEAN DEFAULT FALSE);",
            "CREATE TABLE IF NOT EXISTS languages (id SERIAL PRIMARY KEY, name VARCHAR(50) UNIQUE NOT NULL, code VARCHAR(10) UNIQUE);",
            "CREATE TABLE IF NOT EXISTS product_translations (id SERIAL PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE CASCADE, language_id INTEGER REFERENCES languages(id) ON DELETE CASCADE, translated_name VARCHAR(255) NOT NULL, UNIQUE(product_id, language_id));",
            "ALTER TABLE uoms ADD COLUMN IF NOT EXISTS alias VARCHAR(10) UNIQUE;",
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;",
            "ALTER TABLE product_aliases ADD COLUMN IF NOT EXISTS qty DECIMAL(12, 3) NOT NULL DEFAULT 1.0;",
            "ALTER TABLE product_aliases ADD COLUMN IF NOT EXISTS mrp DECIMAL(12, 3) NOT NULL DEFAULT 0;",
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS mrp DECIMAL(12, 3) NOT NULL DEFAULT 0;",
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS base_uom VARCHAR(20) DEFAULT 'pcs';",
            "ALTER TABLE products ALTER COLUMN price TYPE DECIMAL(12, 3);",
            "ALTER TABLE sale_items ADD COLUMN IF NOT EXISTS uom VARCHAR(20);",
            "ALTER TABLE sale_items ALTER COLUMN quantity TYPE DECIMAL(12, 3);",
            "ALTER TABLE sale_items ALTER COLUMN price_at_sale TYPE DECIMAL(12, 3);",
            "ALTER TABLE sales ALTER COLUMN total_amount TYPE DECIMAL(12, 3);",
            "ALTER TABLE schemes ADD COLUMN IF NOT EXISTS target_uom VARCHAR(20);",
            "ALTER TABLE schemes RENAME COLUMN discount_value TO benefit_value;",
            "ALTER TABLE schemes ADD COLUMN IF NOT EXISTS max_qty DECIMAL(12, 3);",
            "ALTER TABLE schemes DROP COLUMN IF EXISTS product_id;",
            "ALTER TABLE scheme_products ADD COLUMN IF NOT EXISTS min_qty DECIMAL(12, 3) DEFAULT 0;",
            "ALTER TABLE scheme_products ADD COLUMN IF NOT EXISTS max_qty DECIMAL(12, 3);",
            "ALTER TABLE scheme_products ADD COLUMN IF NOT EXISTS target_uom VARCHAR(20);",
            "ALTER TABLE scheme_products ADD COLUMN IF NOT EXISTS benefit_type VARCHAR(20) DEFAULT 'percent';",
            "ALTER TABLE scheme_products ADD COLUMN IF NOT EXISTS benefit_value DECIMAL(12, 3) DEFAULT 0;",
            "ALTER TABLE scheme_products ALTER COLUMN min_qty TYPE DECIMAL(12, 3);",
            "ALTER TABLE scheme_products ALTER COLUMN max_qty TYPE DECIMAL(12, 3);",
            "ALTER TABLE scheme_products ALTER COLUMN benefit_value TYPE DECIMAL(12, 3);",
            "ALTER TABLE sale_items ADD COLUMN IF NOT EXISTS mrp DECIMAL(12, 3);"
        ]

        conn = None
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            for command in commands:
                try:
                    cur.execute(command)
                    conn.commit()
                except psycopg2.Error:
                    conn.rollback()
            for migration in migrations:
                try:
                    cur.execute(migration)
                    conn.commit()
                except psycopg2.Error:
                    conn.rollback()
            
            # Seed default UOMs
            cur.execute("SELECT COUNT(*) FROM uoms")
            if cur.fetchone()[0] == 0:
                default_uoms = ['pcs', 'kg', 'g', 'ltr', 'ml', 'box', 'pkt']
                for u in default_uoms:
                    try:
                        cur.execute("INSERT INTO uoms (name) VALUES (%s)", (u,))
                        conn.commit()
                    except psycopg2.Error:
                        conn.rollback()

            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error initializing database: {error}")
        finally:
            if conn is not None:
                conn.close()

    # ... [UOM Methods] ...
    def add_uom(self, name, alias=None):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO uoms (name, alias) VALUES (%s, %s) 
                   ON CONFLICT (name) DO UPDATE SET alias = COALESCE(EXCLUDED.alias, uoms.alias)""", 
                (name, alias)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding UOM: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    def get_uoms(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, alias FROM uoms ORDER BY name")
        uoms = cur.fetchall()
        cur.close()
        conn.close()
        return uoms

    def get_uom_map(self):
        # Returns a dict mapping alias -> name
        uoms = self.get_uoms()
        mapping = {}
        for _, name, alias in uoms:
            if alias:
                mapping[alias.lower()] = name
        return mapping

    def delete_uom(self, name):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM uoms WHERE name = %s", (name,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            cur.close()
            conn.close()

    # ... [Language Methods] ...
    def add_language(self, name, code=None):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO languages (name, code) VALUES (%s, %s)
                   ON CONFLICT (name) DO UPDATE SET code = EXCLUDED.code""", 
                (name, code)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding language: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def get_languages(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, code FROM languages ORDER BY name")
        langs = cur.fetchall()
        cur.close(); conn.close()
        return langs

    def delete_language(self, lang_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM languages WHERE id = %s", (lang_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            cur.close(); conn.close()

    def add_translation(self, product_id, language_id, translated_name):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO product_translations (product_id, language_id, translated_name) 
                   VALUES (%s, %s, %s) 
                   ON CONFLICT (product_id, language_id) DO UPDATE SET translated_name = EXCLUDED.translated_name""",
                (product_id, language_id, translated_name)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding translation: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def get_translations(self, product_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT l.id, l.name, pt.translated_name 
            FROM product_translations pt
            JOIN languages l ON pt.language_id = l.id
            WHERE pt.product_id = %s
        """, (product_id,))
        trans = cur.fetchall()
        cur.close(); conn.close()
        return trans

    def get_translated_items(self, items, language_id):
        if not language_id:
            return items
        
        conn = self.get_connection()
        cur = conn.cursor()
        translated_items = []
        for item in items:
            cur.execute("SELECT translated_name FROM product_translations WHERE product_id = %s AND language_id = %s", (item['id'], language_id))
            res = cur.fetchone()
            new_item = item.copy()
            if res:
                new_item['name'] = res[0]
            translated_items.append(new_item)
        cur.close(); conn.close()
        return translated_items

    # ... [User Methods] ...
    def add_user(self, username, password, full_name, is_superuser=False):
        import hashlib
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO users (username, password, full_name, is_superuser) VALUES (%s, %s, %s, %s)
                   ON CONFLICT (username) DO UPDATE SET full_name = EXCLUDED.full_name, is_superuser = EXCLUDED.is_superuser""",
                (username, pwd_hash, full_name, is_superuser)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def get_users(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, is_superuser FROM users ORDER BY username")
        users = cur.fetchall()
        cur.close(); conn.close()
        return users

    def delete_user(self, user_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            cur.close(); conn.close()

    def authenticate_user(self, username, password):
        import hashlib
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, is_superuser FROM users WHERE username = %s AND password = %s", (username, pwd_hash))
        user = cur.fetchone()
        cur.close(); conn.close()
        return user

    # ... [Customer Methods] ...
    def add_customer(self, name, mobile, address=None, email=None):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO customers (name, mobile, address, email) VALUES (%s, %s, %s, %s) 
                   ON CONFLICT (mobile) DO UPDATE SET name = EXCLUDED.name, address = EXCLUDED.address, email = EXCLUDED.email
                   RETURNING id""",
                (name, mobile, address, email)
            )
            cid = cur.fetchone()[0]
            conn.commit()
            return cid
        except Exception as e:
            print(f"Error adding customer: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def get_customers(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, mobile, address, email FROM customers ORDER BY name")
        customers = cur.fetchall()
        cur.close(); conn.close()
        return customers

    def search_customers(self, query):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, mobile, address, email FROM customers WHERE name ILIKE %s OR mobile ILIKE %s",
            (f"%{query}%", f"%{query}%")
        )
        customers = cur.fetchall()
        cur.close(); conn.close()
        return customers

    def get_customer_by_mobile(self, mobile):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, mobile, address, email FROM customers WHERE mobile = %s", (mobile,))
        customer = cur.fetchone()
        cur.close(); conn.close()
        return customer

    def delete_customer(self, cid):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM customers WHERE id = %s", (cid,))
            conn.commit()
            return True
        except: return False
        finally: cur.close(); conn.close()

    # ... [Purchase Methods] ...
    def record_purchase(self, supplier_name, invoice_no, items, total_amount, timestamp=None):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            if timestamp:
                cur.execute(
                    "INSERT INTO purchases (supplier_name, invoice_no, total_amount, timestamp) VALUES (%s, %s, %s, %s) RETURNING id",
                    (supplier_name, invoice_no, total_amount, timestamp)
                )
            else:
                cur.execute(
                    "INSERT INTO purchases (supplier_name, invoice_no, total_amount) VALUES (%s, %s, %s) RETURNING id",
                    (supplier_name, invoice_no, total_amount)
                )
            purchase_id = cur.fetchone()[0]

            for item in items:
                cur.execute(
                    "INSERT INTO purchase_items (purchase_id, product_id, quantity, purchase_rate, uom, mrp) VALUES (%s, %s, %s, %s, %s, %s)",
                    (purchase_id, item['pid'], item['qty'], item['rate'], item['uom'], item.get('mrp'))
                )
            
            conn.commit()
            return purchase_id
        except Exception as e:
            conn.rollback()
            print(f"Error recording purchase: {e}")
            return None
        finally:
            cur.close(); conn.close()

    def get_purchase_history(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, timestamp, supplier_name, invoice_no, total_amount FROM purchases ORDER BY timestamp DESC")
        purchases = cur.fetchall()
        cur.close(); conn.close()
        return purchases

    def get_item_purchase_register(self, product_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.timestamp, p.supplier_name, p.invoice_no, pi.quantity, pi.purchase_rate, pi.uom, pi.mrp
            FROM purchase_items pi
            JOIN purchases p ON pi.purchase_id = p.id
            WHERE pi.product_id = %s
            ORDER BY p.timestamp DESC
        """, (product_id,))
        register = cur.fetchall()
        cur.close(); conn.close()
        return register

    def search_purchases_by_item(self, query):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT p.id, p.timestamp, p.supplier_name, p.invoice_no, p.total_amount
            FROM purchases p
            JOIN purchase_items pi ON p.id = pi.purchase_id
            JOIN products pr ON pi.product_id = pr.id
            WHERE pr.name ILIKE %s OR pr.barcode ILIKE %s
            ORDER BY p.timestamp DESC
        """, (f"%{query}%", f"%{query}%"))
        purchases = cur.fetchall()
        cur.close(); conn.close()
        return purchases

    def get_suppliers(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT supplier_name FROM purchases WHERE supplier_name IS NOT NULL ORDER BY supplier_name")
        suppliers = [r[0] for r in cur.fetchall()]
        cur.close(); conn.close()
        return suppliers

    # ... [Held Sales Methods] ...
    def hold_sale(self, items, total_amount, user_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO held_sales (total_amount, user_id) VALUES (%s, %s) RETURNING id",
                (total_amount, user_id)
            )
            held_id = cur.fetchone()[0]

            for item in items:
                cur.execute(
                    "INSERT INTO held_sale_items (held_sale_id, product_id, quantity, price_at_sale, uom, mrp) VALUES (%s, %s, %s, %s, %s, %s)",
                    (held_id, item['id'], item['quantity'], item['price'], item['uom'], item.get('mrp'))
                )
            
            conn.commit()
            return held_id
        except Exception as e:
            conn.rollback()
            print(f"Error holding sale: {e}")
            return None
        finally:
            cur.close(); conn.close()

    def get_held_sales(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT h.id, h.timestamp, h.total_amount, u.username 
            FROM held_sales h
            LEFT JOIN users u ON h.user_id = u.id
            ORDER BY h.timestamp DESC
        """)
        sales = cur.fetchall()
        cur.close(); conn.close()
        return sales

    def get_held_sale_items(self, held_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, hi.quantity, hi.price_at_sale, hi.uom, hi.product_id, p.barcode, hi.mrp
            FROM held_sale_items hi
            JOIN products p ON hi.product_id = p.id
            WHERE hi.held_sale_id = %s
        """, (held_id,))
        items = cur.fetchall()
        cur.close(); conn.close()
        return [{'name': i[0], 'quantity': float(i[1]), 'price': float(i[2]), 'uom': i[3], 'id': i[4], 'barcode': i[5], 'mrp': float(i[6]) if i[6] else 0.0} for i in items]

    def delete_held_sale(self, held_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM held_sales WHERE id = %s", (held_id,))
            conn.commit()
            return True
        except: return False
        finally: cur.close(); conn.close()

    def reindex_database(self):
        conn = self.get_connection()
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute("REINDEX DATABASE " + self.conn_params['dbname'])
            return True
        except Exception as e:
            print(f"Reindex error: {e}")
            return False
        finally:
            cur.close(); conn.close()

    # ... [Existing Product Methods] ...
    def add_product(self, name, barcode, mrp, price, category="General", base_uom="pcs"):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO products (name, barcode, mrp, price, category, base_uom) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (name, barcode, mrp, price, category, base_uom)
            )
            pid = cur.fetchone()[0]
            conn.commit()
            return pid
        except Exception as e:
            print(f"Error adding product: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    def update_product(self, product_id, name, barcode, mrp, price, category, base_uom):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE products SET name=%s, barcode=%s, mrp=%s, price=%s, category=%s, base_uom=%s WHERE id=%s",
                (name, barcode, mrp, price, category, base_uom, product_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating product: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    def add_alias(self, product_id, barcode, uom, mrp, price, factor, qty=1.0):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO product_aliases (product_id, barcode, uom, mrp, price, factor, qty) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (product_id, barcode, uom, mrp, price, factor, qty)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding alias: {e}")
            return False
        finally:
            cur.close()
            conn.close()
            
    def get_aliases(self, product_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, barcode, uom, mrp, price, factor, qty FROM product_aliases WHERE product_id = %s", (product_id,))
        aliases = cur.fetchall()
        cur.close()
        conn.close()
        return aliases

    def delete_alias(self, alias_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM product_aliases WHERE id = %s", (alias_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            cur.close()
            conn.close()

    def delete_product(self, product_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE products SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP WHERE id = %s", (product_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def restore_product(self, product_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE products SET is_deleted = FALSE, deleted_at = NULL WHERE id = %s", (product_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error restoring product: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def get_deleted_products(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, barcode, mrp, price, category, base_uom, deleted_at FROM products WHERE is_deleted = TRUE ORDER BY deleted_at DESC")
        products = cur.fetchall()
        cur.close(); conn.close()
        return products

    def purge_old_deleted_products(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM products WHERE is_deleted = TRUE AND deleted_at < CURRENT_TIMESTAMP - INTERVAL '30 days'")
            conn.commit()
        except Exception as e:
            print(f"Error purging products: {e}")
        finally:
            cur.close(); conn.close()

    def search_products(self, query):
        conn = self.get_connection()
        cur = conn.cursor()
        # Search both products and aliases. Returns matching barcodes.
        cur.execute(
            """
            SELECT id, name, barcode, mrp, price, category, uom FROM (
                SELECT p.id, p.name, p.barcode as barcode, p.mrp, p.price, p.category, p.base_uom as uom,
                       similarity(p.name, %s) as sim_n, similarity(p.barcode, %s) as sim_b, p.is_deleted
                FROM products p
                UNION ALL
                SELECT p.id, p.name, pa.barcode as barcode, pa.mrp, pa.price, p.category, pa.uom as uom,
                       similarity(p.name, %s) as sim_n, similarity(pa.barcode, %s) as sim_b, p.is_deleted
                FROM product_aliases pa
                JOIN products p ON pa.product_id = p.id
            ) as combined
            WHERE (sim_n > 0.15 OR sim_b > 0.15 OR name ILIKE %s OR barcode ILIKE %s) AND is_deleted = FALSE
            ORDER BY GREATEST(sim_n, sim_b) DESC, name
            LIMIT 15
            """,
            (query, query, query, query, f"%{query}%", f"%{query}%")
        )
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products

    def get_all_products(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, barcode, mrp, price, category, base_uom FROM products WHERE is_deleted = FALSE ORDER BY name")
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products

    def find_product_by_barcode(self, barcode):
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, barcode, mrp, price, category, base_uom FROM products WHERE barcode = %s AND is_deleted = FALSE", (barcode,))
        product = cur.fetchone()
        
        if product:
            # (id, name, barcode, mrp, price, category, base_uom, factor, is_alias, qty, base_price, base_mrp)
            res = (product[0], product[1], product[2], product[3], product[4], product[5], product[6], 1.0, False, 1.0, product[4], product[3])
            cur.close(); conn.close()
            return res
            
        cur.execute("""
            SELECT p.id, p.name, a.barcode, a.mrp, a.price, p.category, a.uom, a.factor, a.qty, p.price as base_price, p.mrp as base_mrp
            FROM product_aliases a
            JOIN products p ON a.product_id = p.id
            WHERE a.barcode = %s AND p.is_deleted = FALSE
        """, (barcode,))
        alias = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if alias:
            # (id, name, barcode, mrp, price, category, uom, factor, is_alias, qty, base_price, base_mrp)
            return (alias[0], alias[1], alias[2], alias[3], alias[4], alias[5], alias[6], alias[7], True, alias[8], alias[9], alias[10])
            
        return None

    def find_product_smart(self, query):
        res = self.find_product_by_barcode(query)
        if res: return res
            
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, barcode, mrp, price, category, base_uom FROM products WHERE name ILIKE %s AND is_deleted = FALSE", (query,))
        p = cur.fetchone()
        if p:
            # (id, name, barcode, mrp, price, category, base_uom, factor, is_alias, qty, base_price, base_mrp)
            res = (p[0], p[1], p[2], p[3], p[4], p[5], p[6], 1.0, False, 1.0, p[4], p[3])
            cur.close(); conn.close()
            return res

        cur.execute("SELECT id, name, barcode, mrp, price, category, base_uom FROM products WHERE name ILIKE %s AND is_deleted = FALSE ORDER BY name LIMIT 1", (f"%{query}%",))
        p = cur.fetchone()
        if p:
            res = (p[0], p[1], p[2], p[3], p[4], p[5], p[6], 1.0, False, 1.0, p[4], p[3])
            cur.close(); conn.close()
            return res

        # Fuzzy fallback
        # Check products
        cur.execute("""
            SELECT id, name, barcode, mrp, price, category, base_uom, 
                   GREATEST(similarity(name, %s), similarity(barcode, %s)) as sim
            FROM products 
            WHERE (similarity(name, %s) > 0.3 OR similarity(barcode, %s) > 0.3) AND is_deleted = FALSE
            ORDER BY sim DESC LIMIT 1
        """, (query, query, query, query))
        p_fuzzy = cur.fetchone()

        # Check aliases
        cur.execute("""
            SELECT p.id, p.name, a.barcode, a.mrp, a.price, p.category, a.uom, a.factor, a.qty, p.price as base_price, p.mrp as base_mrp,
                   similarity(a.barcode, %s) as sim
            FROM product_aliases a
            JOIN products p ON a.product_id = p.id
            WHERE similarity(a.barcode, %s) > 0.3 AND p.is_deleted = FALSE
            ORDER BY sim DESC LIMIT 1
        """, (query, query))
        a_fuzzy = cur.fetchone()
        
        cur.close(); conn.close()
        
        if p_fuzzy and a_fuzzy:
            if p_fuzzy[7] >= a_fuzzy[11]:
                return (p_fuzzy[0], p_fuzzy[1], p_fuzzy[2], p_fuzzy[3], p_fuzzy[4], p_fuzzy[5], p_fuzzy[6], 1.0, False, 1.0, p_fuzzy[4], p_fuzzy[3])
            else:
                return (a_fuzzy[0], a_fuzzy[1], a_fuzzy[2], a_fuzzy[3], a_fuzzy[4], a_fuzzy[5], a_fuzzy[6], a_fuzzy[7], True, a_fuzzy[8], a_fuzzy[9], a_fuzzy[10])
        elif p_fuzzy:
            return (p_fuzzy[0], p_fuzzy[1], p_fuzzy[2], p_fuzzy[3], p_fuzzy[4], p_fuzzy[5], p_fuzzy[6], 1.0, False, 1.0, p_fuzzy[4], p_fuzzy[3])
        elif a_fuzzy:
            return (a_fuzzy[0], a_fuzzy[1], a_fuzzy[2], a_fuzzy[3], a_fuzzy[4], a_fuzzy[5], a_fuzzy[6], a_fuzzy[7], True, a_fuzzy[8], a_fuzzy[9], a_fuzzy[10])
            
        return None

    def get_product_uom_data(self, product_id, uom):
        conn = self.get_connection()
        cur = conn.cursor()
        # 1. Check if it is the base UOM
        cur.execute("SELECT base_uom, price, mrp FROM products WHERE id = %s", (product_id,))
        p = cur.fetchone()
        if p and p[0] == uom:
            res = {'price': float(p[1]), 'mrp': float(p[2]), 'factor': 1.0, 'uom': p[0], 'base_price': float(p[1]), 'base_mrp': float(p[2])}
            cur.close(); conn.close()
            return res
        
        # 2. Check aliases
        cur.execute("SELECT price, factor, uom, mrp FROM product_aliases WHERE product_id = %s AND uom = %s", (product_id, uom))
        a = cur.fetchone()
        cur.close(); conn.close()
        if a:
            return {'price': float(a[0]), 'mrp': float(a[3]), 'factor': float(a[1]), 'uom': a[2], 'base_price': float(p[1]) if p else 0.0, 'base_mrp': float(p[2]) if p else 0.0}
        
        return None

    def get_available_mrps(self, product_id, uom):
        conn = self.get_connection()
        cur = conn.cursor()
        res = []
        # Check base product
        cur.execute("SELECT mrp, price FROM products WHERE id = %s AND base_uom = %s", (product_id, uom))
        base = cur.fetchone()
        if base:
            res.append({'mrp': float(base[0]), 'price': float(base[1])})
        
        # Check aliases
        cur.execute("SELECT mrp, price FROM product_aliases WHERE product_id = %s AND uom = %s", (product_id, uom))
        for row in cur.fetchall():
            res.append({'mrp': float(row[0]), 'price': float(row[1])})
        
        cur.close(); conn.close()
        # Return unique pairs
        unique_res = []
        seen = set()
        for item in res:
            pair = (item['mrp'], item['price'])
            if pair not in seen:
                unique_res.append(item)
                seen.add(pair)
        return unique_res

    # ... [Schemes Methods] ...
    def add_scheme(self, name, valid_from, valid_to, items_data):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO schemes (name, valid_from, valid_to) VALUES (%s, %s, %s) RETURNING id",
                (name, valid_from, valid_to)
            )
            scheme_id = cur.fetchone()[0]
            
            for item in items_data:
                cur.execute(
                    """INSERT INTO scheme_products 
                       (scheme_id, product_id, min_qty, max_qty, target_uom, benefit_type, benefit_value) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (scheme_id, item['pid'], item['min_qty'], item['max_qty'], item['target_uom'], 
                     item['benefit_type'], item['benefit_value'])
                )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding scheme: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def update_scheme(self, scheme_id, name, valid_from, valid_to, items_data):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # 1. Update Header
            cur.execute(
                "UPDATE schemes SET name=%s, valid_from=%s, valid_to=%s WHERE id=%s",
                (name, valid_from, valid_to, scheme_id)
            )
            
            # 2. Replace Rules (Delete all and re-insert)
            cur.execute("DELETE FROM scheme_products WHERE scheme_id = %s", (scheme_id,))
            
            for item in items_data:
                cur.execute(
                    """INSERT INTO scheme_products 
                       (scheme_id, product_id, min_qty, max_qty, target_uom, benefit_type, benefit_value) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (scheme_id, item['pid'], item['min_qty'], item['max_qty'], item['target_uom'], 
                     item['benefit_type'], item['benefit_value'])
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating scheme: {e}")
            return False
        finally:
            cur.close(); conn.close()

    def get_scheme_rules(self, scheme_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, p.barcode, sp.min_qty, sp.max_qty, sp.target_uom, sp.benefit_type, sp.benefit_value
            FROM scheme_products sp
            JOIN products p ON sp.product_id = p.id
            WHERE sp.scheme_id = %s
        """, (scheme_id,))
        rules = cur.fetchall()
        cur.close(); conn.close()
        # Returns list of tuples
        return rules

    def get_schemes(self):
        conn = self.get_connection()
        cur = conn.cursor()
        # Aggregation of item details for a summary view
        cur.execute("""
            SELECT s.id, s.name, s.valid_from, s.valid_to,
                   STRING_AGG(p.name || ' (' || sp.min_qty::float || '-' || COALESCE(sp.max_qty::float::text, '∞') || ' ' || COALESCE(sp.target_uom, 'All') || ')', ', ') as details
            FROM schemes s 
            LEFT JOIN scheme_products sp ON s.id = sp.scheme_id
            LEFT JOIN products p ON sp.product_id = p.id
            GROUP BY s.id
            ORDER BY s.id
        """)
        schemes = cur.fetchall()
        cur.close(); conn.close()
        return schemes

    def get_active_scheme_for_product(self, product_id, qty, uom=None):
        conn = self.get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT s.name, sp.benefit_value, sp.benefit_type, sp.target_uom
            FROM schemes s
            JOIN scheme_products sp ON s.id = sp.scheme_id
            WHERE sp.product_id = %s 
              AND s.is_active = TRUE 
              AND %s >= sp.min_qty
              AND (%s <= sp.max_qty OR sp.max_qty IS NULL)
              AND CURRENT_DATE BETWEEN s.valid_from AND COALESCE(s.valid_to, '9999-12-31')
        """
        params = [product_id, qty, qty]
        
        if uom:
            query += " AND (sp.target_uom IS NULL OR sp.target_uom = %s) "
            params.append(uom)
        else:
            query += " AND sp.target_uom IS NULL "

        query += " ORDER BY sp.min_qty DESC, sp.benefit_value DESC LIMIT 1"
        
        cur.execute(query, tuple(params))
        scheme = cur.fetchone()
        cur.close(); conn.close()
        return scheme

    def delete_scheme(self, scheme_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM schemes WHERE id = %s", (scheme_id,))
            conn.commit()
            return True
        except: return False
        finally: cur.close(); conn.close()

    # ... [Sales Methods] ...
    def get_sales_history(self, date=None, query=None):
        conn = self.get_connection()
        cur = conn.cursor()
        
        sql_query = """
            SELECT s.id, s.timestamp, s.total_amount, s.payment_method, c.name as customer_name, c.mobile as customer_mobile
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE 1=1
        """
        params = []
        
        if date:
            sql_query += " AND DATE(s.timestamp) = %s"
            params.append(date)
            
        if query:
            sql_query += " AND (c.name ILIKE %s OR c.mobile ILIKE %s OR s.id::text ILIKE %s)"
            params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
        sql_query += " ORDER BY s.timestamp DESC"
        
        cur.execute(sql_query, tuple(params))
        sales = cur.fetchall()
        cur.close()
        conn.close()
        return sales

    def get_sale_items(self, sale_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, si.quantity, si.price_at_sale, si.uom, si.product_id, p.barcode, si.mrp
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = %s
        """, (sale_id,))
        items = cur.fetchall()
        cur.close()
        conn.close()
        # Format: (name, qty, price, uom, pid, barcode, mrp)
        return [{'name': i[0], 'quantity': float(i[1]), 'price': float(i[2]), 'uom': i[3], 'id': i[4], 'barcode': i[5], 'mrp': float(i[6]) if i[6] else 0.0} for i in items]

    def process_sale(self, items, total_amount, payment_method="Cash", customer_id=None, timestamp=None):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            if timestamp:
                cur.execute(
                    "INSERT INTO sales (total_amount, payment_method, customer_id, timestamp) VALUES (%s, %s, %s, %s) RETURNING id",
                    (total_amount, payment_method, customer_id, timestamp)
                )
            else:
                cur.execute(
                    "INSERT INTO sales (total_amount, payment_method, customer_id) VALUES (%s, %s, %s) RETURNING id",
                    (total_amount, payment_method, customer_id)
                )
            sale_id = cur.fetchone()[0]

            for item in items:
                cur.execute(
                    "INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale, uom, mrp) VALUES (%s, %s, %s, %s, %s, %s)",
                    (sale_id, item['id'], item['quantity'], item['price'], item['uom'], item.get('mrp'))
                )
            
            conn.commit()
            return sale_id
        except Exception as e:
            conn.rollback()
            print(f"Error processing sale: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def update_sale(self, sale_id, items, total_amount, payment_method="Cash", customer_id=None):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # 1. Delete old items
            cur.execute("DELETE FROM sale_items WHERE sale_id = %s", (sale_id,))

            # 2. Update Sales Header
            cur.execute("UPDATE sales SET total_amount = %s, payment_method = %s, customer_id = %s WHERE id = %s", (total_amount, payment_method, customer_id, sale_id))

            # 3. Insert new items
            for item in items:
                cur.execute(
                    "INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale, uom, mrp) VALUES (%s, %s, %s, %s, %s, %s)",
                    (sale_id, item['id'], item['quantity'], item['price'], item['uom'], item.get('mrp'))
                )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating sale: {e}")
            return False
        finally:
            cur.close()
            conn.close()
