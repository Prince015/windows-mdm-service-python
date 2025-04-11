import ctypes
from ctypes import wintypes
import os
import sqlite3
from datetime import datetime

#db path
DB_PATH = os.path.join("data", "app_block.db")

# Constants
FILE_DEVICE_UNKNOWN = 0x00000022
METHOD_BUFFERED = 0
FILE_ANY_ACCESS = 0
MAX_PATH = 260

# CTL_CODE macro equivalent in Python
def CTL_CODE(DeviceType, Function, Method, Access):
    return ((DeviceType << 16) | (Access << 14) | (Function << 2) | Method)

# Define IOCTL code
IOCTL_RECEIVE_APP_LIST = CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_ANY_ACCESS)

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
DEVICE_PATH = r'\\.\PWAppListDevice'

# Load kernel32.dll
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define CreateFile function
CreateFile = kernel32.CreateFileW
CreateFile.argtypes = [
    wintypes.LPCWSTR,  # lpFileName
    wintypes.DWORD,    # dwDesiredAccess
    wintypes.DWORD,    # dwShareMode
    wintypes.LPVOID,   # lpSecurityAttributes
    wintypes.DWORD,    # dwCreationDisposition
    wintypes.DWORD,    # dwFlagsAndAttributes
    wintypes.HANDLE    # hTemplateFile
]
CreateFile.restype = wintypes.HANDLE

# Define DeviceIoControl function
DeviceIoControl = kernel32.DeviceIoControl
DeviceIoControl.argtypes = [
    wintypes.HANDLE,   # hDevice
    wintypes.DWORD,    # dwIoControlCode
    wintypes.LPVOID,   # lpInBuffer
    wintypes.DWORD,    # nInBufferSize
    wintypes.LPVOID,   # lpOutBuffer
    wintypes.DWORD,    # nOutBufferSize
    ctypes.POINTER(wintypes.DWORD),  # lpBytesReturned
    wintypes.LPVOID    # lpOverlapped
]
DeviceIoControl.restype = wintypes.BOOL

# Define CloseHandle function
CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

# Define the APPLICATION_LIST structure
class APPLICATION_LIST(ctypes.Structure):
    _fields_ = [
        ("Count", wintypes.ULONG),
        ("Applications", wintypes.WCHAR * (MAX_PATH * 100))  # Adjust size to accommodate all applications
    ]

def open_device():
    """Open a handle to the kernel device"""
    handle = CreateFile(
        DEVICE_PATH,
        GENERIC_READ | GENERIC_WRITE,
        0,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    
    if handle == wintypes.HANDLE(-1).value:
        error_code = ctypes.get_last_error()
        raise Exception(f"Failed to open device: {error_code}")
    
    return handle


def init_app_block_db():
    """Initialize the SQLite database for app blocking"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT UNIQUE,
            blocked_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def send_app_list_to_block(app_names):
    """Send application list to kernel driver"""
    if not isinstance(app_names, list):
        return {"status": "error", "message": "app_names must be a list"}
        
    if not app_names:
        try:
            # Open the device
            handle = open_device()
            
            # Prepare the application list - empty list
            app_list = APPLICATION_LIST()
            app_list.Count = 0
            app_list.Applications = ''
            
            bytesReturned = wintypes.DWORD()
            
            # Send IOCTL
            success = DeviceIoControl(
                handle,
                IOCTL_RECEIVE_APP_LIST,
                ctypes.byref(app_list),
                ctypes.sizeof(app_list),
                None,
                0,
                ctypes.byref(bytesReturned),
                None
            )
            
            # Close the device handle
            CloseHandle(handle)
            
            if not success:
                error_code = ctypes.get_last_error()
                return {"status": "error", "message": f"Failed to send empty list IOCTL: {error_code}"}
            
            return {"status": "success", "message": "Successfully sent empty application list to kernel driver"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    try:
        # Open the device
        handle = open_device()
        
        # Prepare the application list
        app_list = APPLICATION_LIST()
        app_list.Count = len(app_names)
        
        # Create a buffer for applications
        buffer = []
        for app_name in app_names:
            # Ensure each application name fits within MAX_PATH and is null-terminated
            padded_name = app_name + '\0' * (MAX_PATH - len(app_name))
            buffer.append(padded_name[:MAX_PATH])
        
        # Convert buffer to a single string
        app_list.Applications = ''.join(buffer)
        
        bytesReturned = wintypes.DWORD()
        
        # Send IOCTL
        success = DeviceIoControl(
            handle,
            IOCTL_RECEIVE_APP_LIST,
            ctypes.byref(app_list),
            ctypes.sizeof(app_list),
            None,
            0,
            ctypes.byref(bytesReturned),
            None
        )
        
        # Close the device handle
        CloseHandle(handle)
        
        if not success:
            error_code = ctypes.get_last_error()
            return {"status": "error", "message": f"Failed to send IOCTL: {error_code}"}
        
        return {"status": "success", "message": f"Successfully sent {len(app_names)} applications to kernel driver"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def add_apps_to_block_db(apps):
    """Add apps to the blocked apps database"""
    if not apps:
        return {"status": "success", "message": "No apps to add to database"}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    try:
        for app in apps:
            cursor.execute(
                "INSERT OR REPLACE INTO blocked_apps (app_name, blocked_at) VALUES (?, ?)",
                (app, timestamp)
            )
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Added {len(apps)} apps to block database"}
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return {"status": "error", "message": f"Database error: {str(e)}"}


def remove_apps_from_block_db(apps):
    """Remove apps from the blocked apps database"""
    if not apps:
        return {"status": "success", "message": "No apps to remove from database"}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        for app in apps:
            cursor.execute("DELETE FROM blocked_apps WHERE app_name = ?", (app,))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Removed {len(apps)} apps from block database"}
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return {"status": "error", "message": f"Database error: {str(e)}"}


def get_all_blocked_apps():
    """Get all currently blocked apps from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT app_name FROM blocked_apps")
        apps = [row[0] for row in cursor.fetchall()]
        conn.close()
        return apps
    except sqlite3.Error as e:
        conn.close()
        return []


def unblock_all_apps():
    """Unblock all apps"""
    try:
        all_blocked = get_all_blocked_apps()
        count = len(all_blocked)
        
        unblocked_from_driver = send_app_list_to_block([])
        
        if unblocked_from_driver["status"] == "success":
            db_result = remove_apps_from_block_db(all_blocked)
            
            if db_result["status"] == "success":
                return {"status": "success", "message": f"Unblocked all {count} apps"}
            else:
                return {"status": "partial", "message": f"Unblocked apps in driver but database error: {db_result['message']}"}
        else:
            return unblocked_from_driver
    except Exception as e:
        return {"status": "error", "message": f"Error unblocking all apps: {str(e)}"}


def unblock_apps(app_names):
    """Unblock specific apps"""
    if not app_names:
        return {"status": "error", "message": "No applications specified to unblock"}
    
    try:
        blocked_apps = get_all_blocked_apps()
        
        apps_to_unblock = [app for app in app_names if app in blocked_apps]
        
        if not apps_to_unblock:
            return {"status": "warning", "message": "None of the specified apps are currently blocked"}
        
        new_block_list = [app for app in blocked_apps if app not in apps_to_unblock]
        
        driver_result = send_app_list_to_block(new_block_list)
        
        if driver_result["status"] == "success":
            db_result = remove_apps_from_block_db(apps_to_unblock)
            
            if db_result["status"] == "success":
                return {
                    "status": "success", 
                    "message": f"Successfully unblocked {len(apps_to_unblock)} apps",
                    "unblocked_apps": apps_to_unblock,
                    "remaining_blocked": new_block_list
                }
            else:
                return {
                    "status": "partial", 
                    "message": f"Unblocked apps in driver but database error: {db_result['message']}"
                }
        else:
            return driver_result
    except Exception as e:
        return {"status": "error", "message": f"Error unblocking apps: {str(e)}"}


def block_apps(app_names):
    """Block specific apps"""
    if not app_names:
        return {"status": "error", "message": "No applications specified to block"}
    
    try:
        blocked_apps = get_all_blocked_apps()
        
        new_block_list = list(set(blocked_apps + app_names))
        
        driver_result = send_app_list_to_block(new_block_list)
        
        if driver_result["status"] == "success":
            db_result = add_apps_to_block_db(app_names)
            
            if db_result["status"] == "success":
                return {
                    "status": "success", 
                    "message": f"Successfully blocked {len(app_names)} apps",
                    "blocked_apps": app_names,
                    "total_blocked": new_block_list
                }
            else:
                return {
                    "status": "partial", 
                    "message": f"Blocked apps in driver but database error: {db_result['message']}"
                }
        else:
            return driver_result
    except Exception as e:
        return {"status": "error", "message": f"Error blocking apps: {str(e)}"}


init_app_block_db()