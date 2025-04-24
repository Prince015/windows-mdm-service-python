from core.browser_history.chrome import ChromeHistory
import os

class BraveHistory(ChromeHistory):
    def __init__(self):
        self.history_path = os.path.expandvars(
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\History"
        )
