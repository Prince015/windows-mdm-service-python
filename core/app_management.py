import os
import json
import logging
import psutil
from datetime import datetime, timedelta

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
