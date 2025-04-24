import os
import sqlite3
import json
from datetime import datetime, timedelta
from shutil import copy2
from core.browser_history.base import BrowserHistory

class FirefoxHistory(BrowserHistory):
    def __init__(self):
        profile_base = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
        self.history_path = self._find_history_file(profile_base)

    def _find_history_file(self, base_dir):
        for folder in os.listdir(base_dir):
            if folder.endswith(".default-release"):
                return os.path.join(base_dir, folder, "places.sqlite")
        return None

    def get_history(self):
        if not self.history_path or not os.path.exists(self.history_path):
            return []

        temp_path = self.history_path + "_copy"
        copy2(self.history_path, temp_path)

        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT url, title, last_visit_date
            FROM moz_places
            WHERE last_visit_date IS NOT NULL
        """)

        entries = []
        for url, title, last_visit_date in cursor.fetchall():
            visit_time = datetime(1970, 1, 1) + timedelta(microseconds=last_visit_date)
            if visit_time.date() == datetime.now().date():
                entries.append({
                    "url": url,
                    "title": title,
                    "visit_time": visit_time
                })

        conn.close()
        os.remove(temp_path)
        return entries
