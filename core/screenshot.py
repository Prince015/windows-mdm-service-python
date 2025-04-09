import os
import logging
from datetime import datetime
from PIL import ImageGrab

SCREENSHOT_DIR = os.path.join("data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def capture_screenshot():
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)

        image = ImageGrab.grab()
        image.save(filepath, "PNG")

        logging.info(f"Screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Failed to capture screenshot: {e}")
        return None
