import requests
import time
import threading
import os
from pathlib import Path

import yaml


TARGET = os.getenv(
    "TARGET_URL",
    "http://ecu-service:8080/calculate"
)

LOAD_PROFILE = os.getenv("LOAD_PROFILE", "medium").strip().lower()
PROFILE_CONFIG = Path(os.getenv("LOAD_PROFILE_CONFIG", "/app/config/load_profiles.yaml"))


def get_worker_count(profile, config_path):
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
        profiles = config.get("load_profiles", {})

    if profile not in profiles:
        supported = ", ".join(sorted(profiles)) or "none"
        raise ValueError(
            f"Unknown LOAD_PROFILE '{profile}'. Choose one of: {supported}"
        )

    workers = profiles[profile].get("workers")
    if not isinstance(workers, int) or workers < 1:
        raise ValueError(f"Profile '{profile}' must configure workers as a positive integer")
    return workers


WORKERS = get_worker_count(LOAD_PROFILE, PROFILE_CONFIG)
print(f"Starting rogue load profile={LOAD_PROFILE} workers={WORKERS}", flush=True)


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
