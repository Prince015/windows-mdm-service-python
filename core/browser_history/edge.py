from core.browser_history.chrome import ChromeHistory
import os

class EdgeHistory(ChromeHistory):
    def __init__(self):
        self.history_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\History"
        )
