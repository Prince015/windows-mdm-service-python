import time
import logging

from core import app_monitor, system_control, heartbeat

class WatcherService:
    def __init__(self):
        self.running = False
        self.heartbeat_interval = 60       # seconds
        self.monitor_interval = 10         # seconds
        self.last_heartbeat = time.time()

    def run(self):
        self.running = True
        logging.info("Watcher Service started.")

        while self.running:
            try:
                # Track current app usage
                app_monitor.track_active_app()

                # Every heartbeat_interval seconds, send heartbeat
                if time.time() - self.last_heartbeat >= self.heartbeat_interval:
                    heartbeat.send_heartbeat()
                    self.last_heartbeat = time.time()

                time.sleep(self.monitor_interval)

            except Exception as e:
                logging.error(f"Error in watcher loop: {e}")

    def stop(self):
        self.running = False
        logging.info("Watcher Service stopped.")
