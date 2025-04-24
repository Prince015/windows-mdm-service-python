from core.browser_history.chrome import ChromeHistory
from core.browser_history.edge import EdgeHistory
from core.browser_history.brave import BraveHistory
from core.browser_history.opera import OperaHistory
from core.browser_history.firefox import FirefoxHistory

def get_browser_handler(app_name: str):
    print(app_name)
    app_map = {
        "chrome.exe": ChromeHistory,
        "msedge.exe": EdgeHistory,
        "brave.exe": BraveHistory,
        "opera.exe": OperaHistory,
        "firefox.exe": FirefoxHistory,
    }
    cls = app_map.get(app_name.lower())
    return cls() if cls else None
