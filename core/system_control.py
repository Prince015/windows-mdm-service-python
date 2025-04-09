import os
import logging
import psutil
import ctypes
import subprocess


def lock_workstation():
    try:
        ctypes.windll.user32.LockWorkStation()
        logging.info("Workstation locked.")
    except Exception as e:
        logging.error(f"Failed to lock workstation: {e}")


def shutdown_system():
    try:
        subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
        logging.info("System shutdown initiated.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to shutdown system: {e}")


def get_battery_status():
    try:
        battery = psutil.sensors_battery()
        if battery:
            return {
                "percent": battery.percent,
                "plugged_in": battery.power_plugged
            }
        else:
            return {
                "percent": None,
                "plugged_in": None
            }
    except Exception as e:
        logging.error(f"Failed to get battery status: {e}")
        return None
