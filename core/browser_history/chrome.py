import os
import sqlite3
from datetime import datetime, timedelta
from shutil import copy2
from core.browser_history.base import BrowserHistory

class ChromeHistory(BrowserHistory):
    def __init__(self):
        self.history_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\History"
        )

    def get_history(self):
        return self._parse_history()

    def _parse_history(self):
        if not os.path.exists(self.history_path):
            return []

        temp_path = self.history_path + "_copy"
        copy2(self.history_path, temp_path)

        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT url, title, last_visit_time
            FROM urls
            WHERE last_visit_time > strftime('%s', 'now', 'start of day') * 1000000
        """)

        EPOCH_START = datetime(1601, 1, 1)
        entries = []
        for url, title, last_visit_time in cursor.fetchall():
            visit_time = EPOCH_START + timedelta(microseconds=last_visit_time)
            entries.append({
                "url": url,
                "title": title,
                "visit_time": visit_time
            })

        conn.close()
        os.remove(temp_path)
        return entries
