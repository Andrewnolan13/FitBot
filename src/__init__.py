import sqlite3
from .constants import DB_PATH, CREDS_PATH, DIR
import os
import json

if not os.path.exists(CREDS_PATH):
    input_ = input("Credentials file not found.\nVisit https://dev.fitbit.com/login to create a new app.\nThere you will be given a client_id and client_secret.\nPress Y to continue.")
    if input_.lower() != "y":
        exit(0)
    # HERE THE USER ENTERS THE CLIENT_ID AND CLIENT_SECRET
    client_id = input("Enter client_id: ")
    client_secret = input("Enter client_secret: ")
    # HERE THE USER AGRESS TO SOME STUFF I THINK
    os.system(f"python FitBot/src/fitbit/gather_keys_oauth2.py {client_id} {client_secret}")
    creds = dict(CLIENT_ID=client_id, CLIENT_SECRET=client_secret)
    with open(CREDS_PATH, "w") as f:
        f.write(json.dumps(creds))
    print("Credentials file created successfully. Exiting now. Should work on re-run.")
    exit(0)

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
conn.close()


from .export import FitbitDataDaemon
from .__main__ import main