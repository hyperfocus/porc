"""
PORC Worker: Polls for submitted runs and triggers build/plan/apply actions.
"""
import os
import time
import json
import logging
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'name': record.name,
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

from porc_common.config import DB_PATH

def poll_runs():
    """Poll the DB_PATH directory for submitted runs and trigger actions."""
    while True:
        for fname in os.listdir(DB_PATH):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(DB_PATH, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
            except Exception as e:
                logging.error(f"Failed to read or parse {path}: {e}")
                continue
            if data.get("status") == "submitted":
                logging.info(f"Worker picked up run: {data['run_id']}")
                # TODO: Implement transition or trigger build/plan/apply here
        time.sleep(10)

def healthz():
    """Health check for the worker process."""
    print(json.dumps({"status": "ok"}))
    sys.exit(0)

if __name__ == "__main__":
    """Entry point for the PORC worker process."""
    if len(sys.argv) > 1 and sys.argv[1] == "healthz":
        healthz()
    logging.info("Starting PORC worker...")
    poll_runs()