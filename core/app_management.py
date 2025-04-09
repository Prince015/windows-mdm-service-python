import os
import json
import logging
import psutil
from datetime import datetime, timedelta
import winreg

BLOCK_CONFIG = "config/settings.json"


def load_block_rules():
    try:
        if not os.path.exists(BLOCK_CONFIG):
            return {"blocked_apps": [], "timed_apps": {}}
        with open(BLOCK_CONFIG, "r") as f:
            config = json.load(f)
            return {
                "blocked_apps": config.get("blocked_apps", []),
                "timed_apps": config.get("timed_apps", {})
            }
    except Exception as e:
        logging.error(f"Error loading app block config: {e}")
        return {"blocked_apps": [], "timed_apps": {}}


def block_and_limit_apps():
    rules = load_block_rules()
    now = datetime.now()

    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            app = proc.info['name']

            # Kill blocked apps
            if app in rules["blocked_apps"]:
                proc.kill()
                logging.info(f"Blocked and killed: {app}")

            # Enforce time limit
            if app in rules["timed_apps"]:
                start_time = datetime.fromtimestamp(proc.info['create_time'])
                allowed_minutes = rules["timed_apps"][app]
                if now - start_time > timedelta(minutes=allowed_minutes):
                    proc.kill()
                    logging.info(f"Killed {app} after exceeding {allowed_minutes} minutes")

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            logging.error(f"Error handling app: {e}")

def get_installed_apps():
    """
    Retrieves a list of installed applications from the Windows Registry.
    Returns a list of dictionaries with name and optionally version.
    """
    apps = []
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for path in registry_paths:
            try:
                reg_key = winreg.OpenKey(hive, path)
                for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
                    try:
                        sub_key_name = winreg.EnumKey(reg_key, i)
                        sub_key = winreg.OpenKey(reg_key, sub_key_name)
                        name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                        try:
                            version, _ = winreg.QueryValueEx(sub_key, "DisplayVersion")
                        except FileNotFoundError:
                            version = "Unknown"
                        apps.append({"name": name, "version": version})
                    except (FileNotFoundError, OSError):
                        continue
            except FileNotFoundError:
                continue

    # Remove duplicates and sort
    unique_apps = {app["name"]: app for app in apps}
    return sorted(unique_apps.values(), key=lambda x: x["name"].lower())
