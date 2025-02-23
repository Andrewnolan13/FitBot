import sqlite3

def list_tables(db_path):
    """Lists all tables in the SQLite database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

def show_table_schema(db_path, table_name):
    """Displays the schema of a specific table."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")  # Fixed issue
        return cursor.fetchall()

def main():
    db_path = "data/database.db"  # Change this to your DB file
    tables = list_tables(db_path)

    print("Tables in the database:")
    for table in tables:
        print(f"- {table}")

    print("\nSchemas:")
    for table in tables:
        schema = show_table_schema(db_path, table)
        print(f"\nSchema for {table}:")
        for col in schema:
            cid, name, ctype, notnull, default, pk = col
            print(f"  {name} ({ctype}) - {'PRIMARY KEY' if pk else ''} {'NOT NULL' if notnull else ''}")

if __name__ == "__main__":
    main()
