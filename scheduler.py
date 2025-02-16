import time
import schedule
import threading
from parser import authorize
from config import ADMIN_IDS


def monitor_excursions():
    while True:
        schedule.run_pending()
        time.sleep(1)


def scheduled_monitoring():
    asyncio.run(authorize(ADMIN_IDS[0]))


schedule.every(31).minutes.do(scheduled_monitoring)


monitoring_thread = threading.Thread(target=monitor_excursions)
monitoring_thread.start()
