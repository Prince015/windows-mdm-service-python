from datetime import datetime, timedelta

class Event:
    def __init__(self, timestamp, app_process_name, app_name, window_title, pid, duration=timedelta(seconds=0), url=None):
        self.timestamp = timestamp
        self.app_process_name = app_process_name
        self.app_name = app_name
        self.window_title = window_title
        self.pid = pid
        self.duration = duration
        self.url = url

    def to_row(self):
        return (
            self.timestamp.isoformat(timespec='seconds'),
            self.app_process_name,
            self.app_name,
            self.window_title,
            self.pid,
            int(self.duration.total_seconds()),
            self.url
        )

    def is_equivalent(self, other):
        return (
            self.app_process_name == other.app_process_name and
            self.app_name == other.app_name and
            self.window_title == other.window_title and
            self.pid == other.pid
        )
