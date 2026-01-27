import psycopg2
from database import DatabaseManager


def drop_all_dbs():
    config_params = DatabaseManager.load_config()
    # Connect to 'postgres' to drop other databases
    params = config_params.copy()
    params["dbname"] = "postgres"

    try:
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()

        # Find all databases starting with elytpos_
        cur.execute("SELECT datname FROM pg_database WHERE datname LIKE 'elytpos_%';")
        dbs = [row[0] for row in cur.fetchall()]

        if not dbs:
            print("No elytpos databases found to drop.")
            return

        for db in dbs:
            print(f"Dropping database: {db}...")
            # We need to terminate existing connections before dropping
            cur.execute(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db}' AND pid <> pg_backend_pid();"
            )
            cur.execute(f'DROP DATABASE "{db}";')
            print(f"Database {db} dropped successfully.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error dropping databases: {e}")


if __name__ == "__main__":
    drop_all_dbs()
