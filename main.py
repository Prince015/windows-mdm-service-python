import threading
import time
import logging
from service.watcher_service import WatcherService
from api_server import app

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def run_flask_app():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def main():
    logging.info("Starting PC Controller Watcher Service")

    watcher = WatcherService()

    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        with watcher:
            while watcher:
                watcher.poll_once()
                time.sleep(watcher.monitor_interval)
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
        watcher.stop()


if __name__ == "__main__":
    main()
