from fastapi import FastAPI, Request, Path
from pydantic import BaseModel
from datetime import datetime
import json
import os

from porc_common.config import DB_PATH
from porc_core.render import render_blueprint

app = FastAPI(title="PORC API")

class BlueprintSubmission(BaseModel):
    kind: str
    variables: dict = {}
    schema_version: str | None = None

@app.post("/blueprint")
async def submit_blueprint(payload: BlueprintSubmission):
    run_id = f"porc-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    record = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "submitted",
        "blueprint": payload.dict()
    }
    with open(f"{DB_PATH}/{run_id}.json", "w") as f:
        json.dump(record, f, indent=2)
    return {"run_id": run_id, "status": "submitted"}

@app.post("/run/{run_id}/build")
async def build_from_blueprint(run_id: str = Path(...)):
    meta_file = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_file):
        return {"error": "Run ID not found"}
    with open(meta_file) as f:
        record = json.load(f)
    files = render_blueprint(record["blueprint"])
    out_dir = f"/tmp/porc-runs/{run_id}"
    os.makedirs(out_dir, exist_ok=True)
    for name, content in files.items():
        with open(f"{out_dir}/{name}", "w") as f:
            f.write(content)
    record["status"] = "built"
    with open(meta_file, "w") as f:
        json.dump(record, f, indent=2)
    return {"run_id": run_id, "status": "built"}

from fastapi.responses import JSONResponse
from porc_common.config import RUNS_PATH
import subprocess

@app.post("/run/{run_id}/plan")
async def plan_run(run_id: str):
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(run_dir):
        return JSONResponse(status_code=404, content={"error": "Run files not found"})

    # Trigger `terraform plan`
    result = subprocess.run(
        ["terraform", "plan", "-input=false", "-no-color"],
        cwd=run_dir,
        capture_output=True,
        text=True
    )

    with open(f"{run_dir}/plan.out", "w") as f:
        f.write(result.stdout)

    return {
        "run_id": run_id,
        "status": "planned" if result.returncode == 0 else "plan_failed",
        "output": result.stdout[:2000]  # truncate preview
    }

@app.post("/run/{run_id}/apply")
async def apply_run(run_id: str):
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

    return {
        "run_id": run_id,
        "status": "applied" if result.returncode == 0 else "apply_failed",
        "output": result.stdout[:2000]
    }

@app.get("/run/{run_id}/status")
async def get_status(run_id: str):
    meta_path = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_path):
        return JSONResponse(status_code=404, content={"error": "Run ID not found"})

    with open(meta_path) as f:
        data = json.load(f)

    return {"run_id": run_id, "status": data.get("status", "unknown")}

@app.get("/run/{run_id}/summary")
async def get_summary(run_id: str):
    meta_path = f"{DB_PATH}/{run_id}.json"
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(meta_path):
        return JSONResponse(status_code=404, content={"error": "Run ID not found"})

    with open(meta_path) as f:
        meta = json.load(f)

    summary = {"run_id": run_id, "status": meta.get("status"), "files": {}}
    for fname in os.listdir(run_dir):
        with open(os.path.join(run_dir, fname)) as f:
            summary["files"][fname] = f.read()[:1000]  # truncate file previews

    return summary