from core import app_monitor, heartbeat
import logging
from core.app_block_policy import evaluate_time_policies
import time

class WatcherService:
    def __init__(self, heartbeat_interval=60, monitor_interval=10, policy_check_interval=30):
        self.heartbeat_interval = heartbeat_interval
        self.monitor_interval = monitor_interval
        self.policy_check_interval = policy_check_interval
        self.running = False
        self.last_heartbeat = None
        self.last_policy_check = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __bool__(self):
        return self.running

    def start(self):
        self.running = True
        self.last_heartbeat = time.time()
        self.last_policy_check = time.time()
        logging.info("Watcher Service started.")

    def stop(self):
        if self.running:
            self.running = False
            logging.info("Watcher Service stopped.")

    def poll_once(self):
        """Performs one monitoring cycle, policy check, and heartbeat check."""
        try:
            app_monitor.track_active_app(pulsetime=self.monitor_interval + 1)

            now = time.time()

            if now - self.last_policy_check >= self.policy_check_interval:
                evaluate_time_policies()
                self.last_policy_check = now

            if now - self.last_heartbeat >= self.heartbeat_interval:
                heartbeat.send_heartbeat()
                self.last_heartbeat = now

        except Exception as e:
            logging.error(f"Error in watcher poll: {e}")
