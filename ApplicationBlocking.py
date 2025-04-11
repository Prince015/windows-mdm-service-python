import ctypes
from ctypes import wintypes

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
        ("Applications", wintypes.WCHAR * (MAX_PATH * 3))  # Adjust size to accommodate all applications
    ]

def main():
    # Open the device
    hDevice = CreateFile(
        r'\\.\PWAppListDevice',
        GENERIC_READ | GENERIC_WRITE,
        0,
        None,
        OPEN_EXISTING,
        0,
        None
    )

    if hDevice == wintypes.HANDLE(-1).value:
        error_code = ctypes.get_last_error()
        print(f"Failed to open device: {error_code}")
        return 1

    # Prepare the application list
    app_names = ["Spotify.exe", "WhatsApp.exe"]
    app_list = APPLICATION_LIST()
    app_list.Count = len(app_names)

    # Create a buffer for applications
    buffer = (wintypes.WCHAR * (MAX_PATH * len(app_names)))()
    for i, app_name in enumerate(app_names):
        # Ensure each application name fits within MAX_PATH and is null-terminated
        padded_name = app_name + '\0' * (MAX_PATH - len(app_name))
        buffer[i * MAX_PATH:(i + 1) * MAX_PATH] = padded_name

    # Convert buffer to a single string
    app_list.Applications = ''.join(buffer)

    bytesReturned = wintypes.DWORD()

    # Send IOCTL
    success = DeviceIoControl(
        hDevice,
        IOCTL_RECEIVE_APP_LIST,
        ctypes.byref(app_list),
        ctypes.sizeof(app_list),
        None,
        0,
        ctypes.byref(bytesReturned),
        None
    )

    if not success:
        error_code = ctypes.get_last_error()
        print(f"Failed to send IOCTL: {error_code}")
        CloseHandle(hDevice)
        return 1

    print("Application list sent to kernel driver")

    # Close the device handle
    CloseHandle(hDevice)
    return 0

if __name__ == "__main__":
    main()