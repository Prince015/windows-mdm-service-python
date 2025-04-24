from core.browser_history.chrome import ChromeHistory
import os

class OperaHistory(ChromeHistory):
    def __init__(self):
        self.history_path = os.path.expandvars(
            r"%APPDATA%\Opera Software\Opera Stable\History"
        )
