import os
import json
from datetime import datetime

AUDIT_DIR = "/tmp/porc-audit"
os.makedirs(AUDIT_DIR, exist_ok=True)

def log_event(run_id: str, action: str, metadata: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": run_id,
        "action": action,
        "metadata": metadata
    }
    log_file = os.path.join(AUDIT_DIR, f"{run_id}.log")
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Placeholder: send to DataDog
    send_to_datadog(entry)

    # Placeholder: send to Dynatrace
    send_to_dynatrace(entry)

def send_to_datadog(entry: dict):
    # TODO: Replace with actual DataDog API call or metrics event
    print(f"[DataDog] Event: {entry['action']} for run {entry['run_id']}")

def send_to_dynatrace(entry: dict):
    # TODO: Replace with actual Dynatrace API call or logging mechanism
    print(f"[Dynatrace] Event: {entry['action']} for run {entry['run_id']}")