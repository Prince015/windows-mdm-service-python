import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os
import sys

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FlaskAPIService"
    _svc_display_name_ = "Flask API Windows Service"
    _svc_description_ = "A Windows Service to run the Flask API server."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.run_flask_app()

    def run_flask_app(self):
        # Determine the correct Python executable
        python_executable = sys.executable
        
        if 'pythonservice.exe' in python_executable:
            python_executable = python_executable.replace('pythonservice.exe', 'python.exe')

        script_path = os.path.join(os.path.dirname(__file__), "api_server.py")
        servicemanager.LogInfoMsg(f"Python executable: {python_executable}")
        servicemanager.LogInfoMsg(f"Script path: {script_path}")

        try:
            # Start the Flask app as a subprocess
            self.process = subprocess.Popen(
                [python_executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            servicemanager.LogInfoMsg(f"Started Flask app with PID: {self.process.pid}")

            # Capture output and errors
            stdout, stderr = self.process.communicate()
            servicemanager.LogInfoMsg(f"Flask app stdout: {stdout.decode()}")
            servicemanager.LogInfoMsg(f"Flask app stderr: {stderr.decode()}")

            # Check for errors
            if self.process.returncode is not None and self.process.returncode != 0:
                servicemanager.LogErrorMsg(f"Flask app failed with return code: {self.process.returncode}")

        except Exception as e:
            servicemanager.LogErrorMsg(f"Exception occurred: {str(e)}")

        # Wait until the service is stopped
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(FlaskService)