from .export import FitbitDataDaemon
from .__main__ import main
import sqlite3
from .constants import DB_PATH

with sqlite3.connect(DB_PATH) as conn:
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