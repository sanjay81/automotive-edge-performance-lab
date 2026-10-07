import requests
import time
import threading
import os


TARGET = os.getenv(
    "TARGET_URL",
    "http://ecu-service:8080/calculate"
)

WORKERS = int(os.getenv("WORKERS", "4"))


def generate_load(worker_id):
    while True:
        try:
            response = requests.get(
                TARGET,
                timeout=10
            )

            print(
                f"worker={worker_id} "
                f"status={response.status_code}"
            )

        except Exception as error:
            print(
                f"worker={worker_id} "
                f"error={error}"
            )

            time.sleep(1)


threads = []

for worker_id in range(WORKERS):

    thread = threading.Thread(
        target=generate_load,
        args=(worker_id,),
        daemon=True
    )

    thread.start()

    threads.append(thread)


while True:
    time.sleep(10)