import winreg
import logging

USB_REG_PATH = r"SYSTEM\CurrentControlSet\Services\USBSTOR"


def set_usb_state(enable: bool):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, USB_REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3 if enable else 4)
        winreg.CloseKey(key)
        logging.info("USB ports {}".format("enabled" if enable else "disabled"))
    except PermissionError:
        logging.error("Permission denied: Run as Administrator to modify USB settings.")
    except Exception as e:
        logging.error(f"Error changing USB state: {e}")


def is_usb_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, USB_REG_PATH, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "Start")
        winreg.CloseKey(key)
        return value == 3
    except Exception as e:
        logging.error(f"Error checking USB state: {e}")
        return None
