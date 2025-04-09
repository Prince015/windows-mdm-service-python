import logging
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join("data", "usage.db")


def init_heartbeat_table():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS heartbeat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()


def send_heartbeat():
    timestamp = datetime.now().isoformat(timespec='seconds')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO heartbeat (timestamp) VALUES (?)', (timestamp,))
    conn.commit()
    conn.close()
    logging.info(f"Heartbeat sent at {timestamp}")


# Initialize table on import
init_heartbeat_table()
