import threading
import time
import logging

from service.watcher_service import WatcherService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    logging.info("Starting PC Controller Watcher Service")

    # Create and start the watcher service
    watcher = WatcherService()
    watcher_thread = threading.Thread(target=watcher.run, daemon=True)
    watcher_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping service...")
        watcher.stop()


if __name__ == "__main__":
    main()
