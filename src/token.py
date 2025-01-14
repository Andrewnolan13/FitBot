import time
import threading
import datetime as dt
from requests.exceptions import ConnectionError

from .constants import REFRESH_TIME, DAEMON_SLEEP
from .utils import sleep

class FitbitTokenDaemon(threading.Thread):
    def __init__(self, fitbitServer, refresh_time: int = REFRESH_TIME, percentage: float = 0.8, sleep_interval: int = DAEMON_SLEEP):
        super().__init__()
        self.fitbitServer = fitbitServer
        self.refresh_time = refresh_time
        self.percentage = percentage
        self.sleep_interval = sleep_interval
        self._stop_event = threading.Event()

    def run(self):
        while self.fitbitServer.running:
            report = "[{}] ".format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            try:
                # Refresh token if it's about to expire
                report += "FitbitTokenDaemon 'Token expires in: {:,.0f}s'".format(self.fitbitServer.client.session.token['expires_at'] - time.time())
                if self.fitbitServer.client.session.token['expires_at'] - self.refresh_time * (1 - self.percentage) < time.time():
                    report += "\n\t\tFitbitTokenDaemon 'Refreshing Token'"
                    self.fitbitServer.client.refresh_token()
            except ConnectionError:
                report += "FitbitTokenDaemon encountered a ConnectionError."
                self.fitbitServer.__authenticate()
            except Exception as e:
                report += f"FitbitTokenDaemon encountered an error: {e}"
            finally:
                print(report)
                sleep(self.sleep_interval)
    
    def stop(self):
        self._stop_event.set()
        self.join()
        print("FitbitTokenDaemon stopped.")