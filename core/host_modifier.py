import os
import logging

HOSTS_PATH = r"C:\\Windows\\System32\\drivers\\etc\\hosts"
REDIRECT_IP = "127.0.0.1"


def read_blocked_sites():
    try:
        if not os.path.exists("config/settings.json"):
            return []
        import json
        with open("config/settings.json", "r") as f:
            settings = json.load(f)
            return settings.get("blocked_websites", [])
    except Exception as e:
        logging.error(f"Error reading blocked websites: {e}")
        return []


def block_websites():
    sites_to_block = read_blocked_sites()
    if not sites_to_block:
        return

    try:
        with open(HOSTS_PATH, "r+") as file:
            content = file.read()
            for site in sites_to_block:
                entry = f"{REDIRECT_IP} {site}"
                if entry not in content:
                    file.write(f"\n{entry}")
        logging.info("Blocked websites successfully updated.")
    except PermissionError:
        logging.error("Permission denied: Run as Administrator to modify hosts file.")
    except Exception as e:
        logging.error(f"Error updating hosts file: {e}")


def unblock_websites():
    try:
        sites_to_block = read_blocked_sites()
        if not sites_to_block:
            return

        with open(HOSTS_PATH, "r") as file:
            lines = file.readlines()

        with open(HOSTS_PATH, "w") as file:
            for line in lines:
                if not any(site in line for site in sites_to_block):
                    file.write(line)

        logging.info("Unblocked websites successfully.")
    except Exception as e:
        logging.error(f"Error unblocking websites: {e}")
