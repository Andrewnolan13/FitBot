from src import main
import sqlite3
from src.constants import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS fitbit (
        scrapeTime TEXT,
        dateTime TEXT,
        steps INTEGER,
        weight REAL,
        calories INTEGER,
        carbs INTEGER,
        fat INTEGER,
        protein INTEGER,
        sodium INTEGER
    );
""")
conn.commit()
print("Table created successfully.")
conn.close()

if __name__ == '__main__':
    main()
