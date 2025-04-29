import win32gui
import win32process
import psutil
import os
import sqlite3
from datetime import datetime, timedelta
from core.event import Event
from core.browser_history.utils import get_browser_handler

DB_PATH = os.path.join("data", "usage.db")
last_event = None
url_attempts = 0  # Track attempts to fetch URL for same event


def get_active_window_info():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        app_name = process.name()
        window_title = win32gui.GetWindowText(hwnd)
        return app_name, window_title, pid
    except Exception:
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
            pid INTEGER,
            duration INTEGER,
            url TEXT
        )
    ''')
    conn.commit()
    conn.close()


def track_active_app(pulsetime=11):
    global last_event, url_attempts
    pulsetime = timedelta(seconds=pulsetime)

    app_name, window_title, pid = get_active_window_info()
    if not app_name:
        return

    now = datetime.now()
    current_event = Event(now, app_name, window_title, pid)

    matched_url = None
    if last_event and last_event.is_equivalent(current_event):
        end_of_last = last_event.timestamp + last_event.duration
        if now <= end_of_last + pulsetime:
            last_event.duration = max(
                last_event.duration,
                now - last_event.timestamp
            )

            if not last_event.url and url_attempts < 5:
                handler = get_browser_handler(app_name)
                if handler:
                    matched_url = handler.match_event(current_event)
                    if matched_url:
                        last_event.url = matched_url
                    url_attempts += 1
                else:
                    url_attempts += 1

            replace_last_event(last_event)
            return

    # New event
    current_event.duration = timedelta(seconds=0)
    handler = get_browser_handler(app_name)
    if handler:
        matched_url = handler.match_event(current_event)
        if matched_url:
            current_event.url = matched_url
    url_attempts = 1 if not matched_url else 0

    insert_event(current_event)
    last_event = current_event


def replace_last_event(event: Event):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE app_usage
        SET timestamp=?, app_name=?, window_title=?, pid=?, duration=?, url=?
        WHERE id=(SELECT MAX(id) FROM app_usage)
    ''', event.to_row())
    conn.commit()
    conn.close()


def insert_event(event: Event):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO app_usage (timestamp, app_name, window_title, pid, duration, url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', event.to_row())
    conn.commit()
    conn.close()


def get_app_usage_today(app_name):
    """Get total usage time for an app today from the app_usage table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    try:
        cursor.execute("""
            SELECT SUM(duration) FROM app_usage 
            WHERE app_name = ? AND timestamp LIKE ?
        """, (app_name, f"{today}%"))

        result = cursor.fetchone()[0]
        conn.close()

        if result:
            return int(result)
        return 0
    except sqlite3.Error as e:
        print(f"Database error getting app usage: {str(e)}")
        conn.close()
        return 0


def get_all_app_usage_today():
    """Get total usage time for all apps today from the app_usage table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    try:
        cursor.execute("""
            SELECT app_name, SUM(duration) FROM app_usage 
            WHERE timestamp LIKE ?
            GROUP BY app_name
        """, (f"{today}%",))

        results = cursor.fetchall()
        conn.close()

        usage_dict = {app: int(duration)
                      for app, duration in results if duration}
        return usage_dict

    except sqlite3.Error as e:
        print(f"Database error getting all app usage: {str(e)}")
        conn.close()
        return {}


init_db()
