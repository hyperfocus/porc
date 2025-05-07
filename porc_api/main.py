"""
PORC API: FastAPI service for blueprint submission, build, plan, apply, and status endpoints.
"""
import json
import os
import re
import logging
import sys
from datetime import datetime
from fastapi import FastAPI, Request, Path
from pydantic import BaseModel
from porc_common.config import DB_PATH
from porc_core.render import render_blueprint
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI(title="PORC API")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = AsyncIOMotorClient(MONGO_URI) if MONGO_URI else None
mongo_db = mongo_client.get_default_database() if mongo_client else None

TRUNCATE_OUTPUT = 2000

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

SAFE_RUNID_RE = re.compile(r"^[\w\-]+$")

def sanitize_run_id(run_id: str):
    """Sanitize and validate run_id to prevent path traversal and invalid characters."""
    if not SAFE_RUNID_RE.match(run_id):
        logging.error(f"Invalid run_id: {run_id}")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": "Invalid run_id"})
    return None

class BlueprintSubmission(BaseModel):
    kind: str
    variables: dict = {}
    schema_version: str | None = None

@app.get("/")
async def root():
    return {"status": "alive"}

@app.get("/healthz")
async def healthz():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"status": "ok"})

@app.post("/blueprint")
async def submit_blueprint(payload: BlueprintSubmission):
    """Submit a new blueprint and create a run record. Stores in MongoDB if configured."""
    try:
        run_id = f"porc-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        record = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "submitted",
            "blueprint": payload.model_dump(mode='json')
        }
        # Store in MongoDB if available
        if mongo_db is not None:
            result = await mongo_db.blueprints.insert_one(record)
            # Convert ObjectId to string for JSON serialization
            record["_id"] = str(result.inserted_id)
            logging.info(f"Blueprint stored in MongoDB: {run_id}")
        # Still write to file for now as backup
        meta_file = f"{DB_PATH}/{run_id}.json"
        tmp_file = meta_file + ".tmp"
        os.makedirs(DB_PATH, exist_ok=True)  # Ensure directory exists
        with open(tmp_file, "w") as f:
            json.dump(record, f, indent=2)
        os.replace(tmp_file, meta_file)
        logging.info(f"Blueprint submitted: {run_id}")
        return {"run_id": run_id, "status": "submitted"}
    except Exception as e:
        logging.error(f"Error submitting blueprint: {str(e)}", exc_info=True)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to submit blueprint", "details": str(e)}
        )

@app.post("/run/{run_id}/build")
async def build_from_blueprint(run_id: str = Path(...)):
    """Build files from a submitted blueprint for a given run_id."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    meta_file = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_file):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Run ID not found"})
    with open(meta_file) as f:
        record = json.load(f)
    files = render_blueprint(record["blueprint"])
    from porc_common.config import RUNS_PATH
    out_dir = f"{RUNS_PATH}/{run_id}"
    os.makedirs(out_dir, exist_ok=True)
    for name, content in files.items():
        with open(f"{out_dir}/{name}", "w") as f:
            f.write(content)
    record["status"] = "built"
    tmp_file = meta_file + ".tmp"
    with open(tmp_file, "w") as f:
        json.dump(record, f, indent=2)
    os.replace(tmp_file, meta_file)
    logging.info(f"Blueprint built: {run_id}")
    return {"run_id": run_id, "status": "built"}

from fastapi.responses import JSONResponse
from porc_common.config import RUNS_PATH
import subprocess

@app.post("/run/{run_id}/plan")
async def plan_run(run_id: str):
    """Run 'terraform plan' for the given run_id."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(run_dir):
        return JSONResponse(status_code=404, content={"error": "Run files not found"})
    result = subprocess.run(
        ["terraform", "plan", "-input=false", "-no-color"],
        cwd=run_dir,
        capture_output=True,
        text=True
    )
    with open(f"{run_dir}/plan.out", "w") as f:
        f.write(result.stdout)
    logging.info(f"Terraform plan for run_id {run_id} (returncode={result.returncode})")
    return {
        "run_id": run_id,
        "status": "planned" if result.returncode == 0 else "plan_failed",
        "output": result.stdout[:TRUNCATE_OUTPUT]
    }

@app.post("/run/{run_id}/apply")
async def apply_run(run_id: str):
    """Run 'terraform apply' for the given run_id."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(run_dir):
        return JSONResponse(status_code=404, content={"error": "Run files not found"})
    result = subprocess.run(
        ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"],
        cwd=run_dir,
        capture_output=True,
        text=True
    )
    with open(f"{run_dir}/apply.out", "w") as f:
        f.write(result.stdout)
    logging.info(f"Terraform apply for run_id {run_id} (returncode={result.returncode})")
    return {
        "run_id": run_id,
        "status": "applied" if result.returncode == 0 else "apply_failed",
        "output": result.stdout[:TRUNCATE_OUTPUT]
    }

@app.get("/run/{run_id}/status")
async def get_status(run_id: str):
    """Get the status of a run by run_id."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    meta_path = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_path):
        return JSONResponse(status_code=404, content={"error": "Run ID not found"})
    with open(meta_path) as f:
        data = json.load(f)
    return {"run_id": run_id, "status": data.get("status", "unknown")}

@app.get("/run/{run_id}/summary")
async def get_summary(run_id: str):
    """Get a summary of a run, including status and file previews."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    meta_path = f"{DB_PATH}/{run_id}.json"
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(meta_path):
        return JSONResponse(status_code=404, content={"error": "Run ID not found"})
    if not os.path.exists(run_dir):
        return JSONResponse(status_code=404, content={"error": "Run files not found"})
    with open(meta_path) as f:
        meta = json.load(f)
    summary = {"run_id": run_id, "status": meta.get("status"), "files": {}}
    for fname in os.listdir(run_dir):
        with open(os.path.join(run_dir, fname)) as f:
            summary["files"][fname] = f.read()[:1000]  # truncate file previews
    return summary
