import os
import logging

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"


def read_blocked_websites():
    blocked = []
    try:
        with open(HOSTS_PATH, "r") as file:
            for line in file:
                if line.startswith(REDIRECT_IP):
                    parts = line.strip().split()
                    if len(parts) > 1:
                        blocked.append(parts[1])
    except Exception as e:
        logging.error(f"Failed to read hosts file: {e}")
    return blocked


def block_websites(websites):
    try:
        with open(HOSTS_PATH, "a") as file:
            for site in websites:
                file.write(f"{REDIRECT_IP} {site}\n")
        logging.info(f"Blocked websites: {websites}")
    except Exception as e:
        logging.error(f"Failed to block websites: {e}")


def unblock_websites(websites):
    try:
        if not os.path.exists(HOSTS_PATH):
            return
        with open(HOSTS_PATH, "r") as file:
            lines = file.readlines()

        with open(HOSTS_PATH, "w") as file:
            for line in lines:
                if not any(line.strip().endswith(site) and line.startswith(REDIRECT_IP) for site in websites):
                    file.write(line)
        logging.info(f"Unblocked websites: {websites}")
    except Exception as e:
        logging.error(f"Failed to unblock websites: {e}")
