import win32gui
import win32process
import psutil
import time
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join("data", "usage.db")


def get_active_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        app_name = process.name()
        window_title = win32gui.GetWindowText(hwnd)
        return app_name, window_title, pid
    except Exception as e:
        return None, None, None


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            app_name TEXT,
            window_title TEXT,
            pid INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def log_app_usage(app_name, window_title, pid):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat(timespec='seconds')
    cursor.execute('''
        INSERT INTO app_usage (timestamp, app_name, window_title, pid)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, app_name, window_title, pid))
    conn.commit()
    conn.close()


def track_active_app():
    app_name, window_title, pid = get_active_window_info()
    if app_name:
        log_app_usage(app_name, window_title, pid)


# Initialize DB on module import
init_db()
