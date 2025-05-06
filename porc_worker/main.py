import os
import time
import json
from porc_common.config import DB_PATH

def poll_runs():
    while True:
        for fname in os.listdir(DB_PATH):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(DB_PATH, fname)
            with open(path) as f:
                data = json.load(f)
            if data.get("status") == "submitted":
                print(f"Worker picked up run: {data['run_id']}")
                # Placeholder: transition or trigger build/plan/apply
        time.sleep(10)

if __name__ == "__main__":
    print("Starting PORC worker...")
    poll_runs()