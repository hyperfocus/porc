
def verify_token(request: Request):
    expected_token = os.getenv("PORC_AUTH_TOKEN")
    auth_header = request.headers.get("Authorization")
    if not expected_token or not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.split(" ", 1)[1]
    if token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid token")



from fastapi import FastAPI, Request, Path, HTTPException, Depends

from porc_core.render import render_blueprint
import os
import json
from datetime import datetime

app = FastAPI(title="PORC API")

DB_PATH = "/tmp/porc-metadata"
RUNS_PATH = "/tmp/porc-runs"
os.makedirs(DB_PATH, exist_ok=True)
os.makedirs(RUNS_PATH, exist_ok=True)

@app.post("/blueprint")
async def submit_blueprint(request: Request, _: None = Depends(verify_token)):
    blueprint = await request.json()
    run_id = f"porc-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    record = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "submitted",
        "blueprint": blueprint
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
        data = json.load(f)
    blueprint = data["blueprint"]

    rendered = render_blueprint(blueprint)
    run_dir = f"{RUNS_PATH}/{run_id}"
    os.makedirs(run_dir, exist_ok=True)

    for name, content in rendered.items():
        with open(os.path.join(run_dir, name), "w") as f:
            f.write(content)

    data["status"] = "rendered"
    data["rendered_files"] = list(rendered.keys())
    data["updated"] = datetime.utcnow().isoformat()

    with open(meta_file, "w") as f:
        json.dump(data, f, indent=2)

    return {"run_id": run_id, "status": "rendered", "files": list(rendered.keys())}
from porc_core.tfe import get_workspace_id, create_config_version, upload_files, trigger_plan_run
import tarfile

@app.post("/run/{run_id}/plan")
async def run_plan(run_id: str = Path(...)):
    meta_file = f"{DB_PATH}/{run_id}.json"
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(meta_file):
        return {"error": "Run ID not found"}
    if not os.path.exists(run_dir):
        return {"error": "Run has not been built/rendered"}

    with open(meta_file) as f:
        data = json.load(f)
    if data["status"] != "rendered":
        return {"error": "Blueprint must be built before planning"}

    # Tarball the config
    archive_path = f"{run_dir}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for f in os.listdir(run_dir):
            tar.add(os.path.join(run_dir, f), arcname=f)

    workspace_name = data["blueprint"].get("metadata", {}).get("repo", run_id)
    try:
        workspace_id = get_workspace_id(workspace_name)
        config_id, upload_url = create_config_version(workspace_id)
        upload_files(upload_url, archive_path)
        tfe_run_id = trigger_plan_run(workspace_id, config_id)
    except Exception as e:
        return {"error": str(e)}

    from porc_core.github_checks import post_check
external_id = data["blueprint"].get("metadata", {}).get("external_id", "")
post_check(run_id, external_id, "PORC Plan", "success", "Terraform plan was queued successfully.")
data["status"] = "plan_queued"
    data["plan_started"] = datetime.utcnow().isoformat()
    data["tfe_run_id"] = tfe_run_id

    with open(meta_file, "w") as f:
        json.dump(data, f, indent=2)

    return {"run_id": run_id, "tfe_run_id": tfe_run_id, "status": "plan_queued"}

@app.post("/run/{run_id}/apply")
async def run_apply(run_id: str = Path(...)):
    meta_file = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_file):
        return {"error": "Run ID not found"}

    with open(meta_file) as f:
        data = json.load(f)

    if data["status"] not in ["plan_queued", "planned"]:
        return {"error": "Plan must be queued before apply"}

    blueprint = data.get("blueprint", {})
    metadata = blueprint.get("metadata", {})
    approval_required = metadata.get("approval_required", False)

    if approval_required and not data.get("approval"):
        return {"error": "Approval required but not found"}

    tfe_run_id = data.get("tfe_run_id")
    if not tfe_run_id:
        return {"error": "Missing Terraform run ID"}

    try:
        url = f"{TFE_HOST}/runs/{tfe_run_id}/actions/apply"
        r = requests.post(url, headers=headers)
        r.raise_for_status()
    except Exception as e:
        return {"error": f"Terraform apply failed: {str(e)}"}

    from porc_core.github_checks import post_check
external_id = data["blueprint"].get("metadata", {}).get("external_id", "")
post_check(run_id, external_id, "PORC Apply", "success", "Terraform apply was triggered.")
data["status"] = "apply_queued"
    data["apply_started"] = datetime.utcnow().isoformat()

    with open(meta_file, "w") as f:
        json.dump(data, f, indent=2)

    return {"run_id": run_id, "status": "apply_queued", "tfe_run_id": tfe_run_id}

import subprocess

@app.post("/run/{run_id}/notify")
async def notify_port(run_id: str = Path(...)):
    meta_file = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_file):
        return {"error": "Run ID not found"}

    with open(meta_file) as f:
        data = json.load(f)

    run_dir = f"{RUNS_PATH}/{run_id}/port_notify"
    os.makedirs(run_dir, exist_ok=True)
    log_file = f"/tmp/porc-logs/{run_id}.log.jsonl"
    os.makedirs("/tmp/porc-logs", exist_ok=True)

    tf_file = f"""
provider "port" {{}}

resource "port_entity" "porc_run" {{
  identifier = var.identifier
  title      = "PORC Run ${{var.identifier}}"
  blueprint  = "porc_run"

  properties = {{
    status        = var.status
    started_at    = var.started_at
    finished_at   = var.finished_at
    external_id   = var.external_id
    change_record = var.change_record
  }}
}}
"""

    tfvars = {
        "identifier": data.get("run_id"),
        "status": data.get("status"),
        "started_at": data.get("plan_started"),
        "finished_at": data.get("apply_started"),
        "external_id": data.get("blueprint", {}).get("metadata", {}).get("external_id", ""),
        "change_record": data.get("approval", {}).get("change_record", "")
    }

    with open(f"{run_dir}/port_notify.tf", "w") as f:
        f.write(tf_file)

    with open(f"{run_dir}/port_notify.tfvars.json", "w") as f:
        json.dump(tfvars, f, indent=2)

    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"

    try:
        subprocess.run(["terraform", "init"], cwd=run_dir, check=True, env=env)
        subprocess.run(["terraform", "apply", "-auto-approve", "-var-file=port_notify.tfvars.json"], cwd=run_dir, check=True, env=env)
        status = "success"
        err = None
    except subprocess.CalledProcessError as e:
        status = "failed"
        err = str(e)

    log_event = {
        "event": "port_sync",
        "run_id": run_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "error": err
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_event) + "\n")

    data["sync_status"] = status
    data["last_sync_time"] = log_event["timestamp"]

    with open(meta_file, "w") as f:
        json.dump(data, f, indent=2)

    if status == "failed":
        return {"status": "port_sync_failed", "error": err}
    return {"status": "port_sync_success", "run_id": run_id}
async def notify_port(run_id: str = Path(...)):
    meta_file = f"{DB_PATH}/{run_id}.json"
    if not os.path.exists(meta_file):
        return {"error": "Run ID not found"}

    with open(meta_file) as f:
        data = json.load(f)

    run_dir = f"{RUNS_PATH}/{run_id}/port_notify"
    os.makedirs(run_dir, exist_ok=True)

    tf_file = f"""
provider "port" {{}}

resource "port_entity" "porc_run" {{
  identifier = var.identifier
  title      = "PORC Run ${{var.identifier}}"
  blueprint  = "porc_run"

  properties = {{
    status        = var.status
    started_at    = var.started_at
    finished_at   = var.finished_at
    external_id   = var.external_id
    change_record = var.change_record
  }}
}}
"""

    tfvars = {
        "identifier": data.get("run_id"),
        "status": data.get("status"),
        "started_at": data.get("plan_started"),
        "finished_at": data.get("apply_started"),  # Placeholder
        "external_id": data.get("blueprint", {}).get("metadata", {}).get("external_id", ""),
        "change_record": data.get("approval", {}).get("change_record", "")
    }

    with open(f"{run_dir}/port_notify.tf", "w") as f:
        f.write(tf_file)

    with open(f"{run_dir}/port_notify.tfvars.json", "w") as f:
        json.dump(tfvars, f, indent=2)

    # Run terraform apply
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "1"

    try:
        subprocess.run(["terraform", "init"], cwd=run_dir, check=True, env=env)
        subprocess.run(["terraform", "apply", "-auto-approve", "-var-file=port_notify.tfvars.json"], cwd=run_dir, check=True, env=env)
    except subprocess.CalledProcessError as e:
        return {"error": f"Terraform apply failed: {e}"}

    return {"status": "port_sync_complete", "run_id": run_id}

@app.get("/run/{run_id}/logs")
async def get_logs(run_id: str = Path(...)):
    log_file = f"/tmp/porc-logs/{run_id}.log.jsonl"
    if not os.path.exists(log_file):
        return {"error": "No logs found"}
    with open(log_file) as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines]

@app.get("/metrics")
async def get_metrics():
    from glob import glob
    total_runs = 0
    successful_applies = 0
    failed_applies = 0
    port_sync_success = 0
    port_sync_failed = 0
    approval_required = 0
    auto_approved = 0
    plan_durations = []
    apply_durations = []

    for path in glob(f"{DB_PATH}/*.json"):
        with open(path) as f:
            data = json.load(f)
        total_runs += 1
        status = data.get("status")
        if status == "apply_queued":
            successful_applies += 1
        if status == "apply_failed":
            failed_applies += 1

        sync = data.get("sync_status")
        if sync == "success":
            port_sync_success += 1
        elif sync == "failed":
            port_sync_failed += 1

        blueprint = data.get("blueprint", {})
        if blueprint.get("metadata", {}).get("approval_required"):
            approval_required += 1
        else:
            auto_approved += 1

        # Plan duration
        try:
            start = datetime.fromisoformat(data.get("plan_started"))
            end = datetime.fromisoformat(data.get("apply_started"))
            plan_durations.append((end - start).total_seconds())
        except:
            pass

        # Apply duration (placeholder - requires apply_finished)
        # add more when available

    return {
        "total_runs": total_runs,
        "successful_applies": successful_applies,
        "failed_applies": failed_applies,
        "port_sync_success": port_sync_success,
        "port_sync_failed": port_sync_failed,
        "approval_required": approval_required,
        "auto_approved": auto_approved,
        "avg_plan_duration_sec": round(sum(plan_durations)/len(plan_durations), 1) if plan_durations else 0,
        "avg_apply_duration_sec": 0  # future placeholder
    }

@app.get("/report/{run_id}")
async def report_run(run_id: str = Path(...)):
    import base64
    meta_file = f"{DB_PATH}/{run_id}.json"
    log_file = f"/tmp/porc-logs/{run_id}.log.jsonl"
    run_dir = f"{RUNS_PATH}/{run_id}"

    if not os.path.exists(meta_file):
        return {"error": "Metadata not found"}

    with open(meta_file) as f:
        metadata = json.load(f)

    logs = []
    if os.path.exists(log_file):
        with open(log_file) as f:
            logs = [json.loads(line) for line in f.readlines()]

    rendered_files = {}
    if os.path.exists(run_dir):
        for filename in os.listdir(run_dir):
            path = os.path.join(run_dir, filename)
            with open(path) as f:
                rendered_files[filename] = f.read()

    return {
        "run_id": run_id,
        "status": metadata.get("status"),
        "sync_status": metadata.get("sync_status"),
        "approval": metadata.get("approval", {}),
        "blueprint": metadata.get("blueprint", {}),
        "plan_started": metadata.get("plan_started"),
        "apply_started": metadata.get("apply_started"),
        "last_sync_time": metadata.get("last_sync_time"),
        "logs": logs,
        "rendered_files": rendered_files
    }

@app.get("/report/summary")
async def report_summary():
    from glob import glob
    summaries = []
    for path in glob(f"{DB_PATH}/*.json"):
        with open(path) as f:
            data = json.load(f)
        summaries.append({
            "run_id": data.get("run_id"),
            "status": data.get("status"),
            "sync_status": data.get("sync_status"),
            "approval_required": bool(data.get("blueprint", {}).get("metadata", {}).get("approval_required")),
            "repo": data.get("blueprint", {}).get("metadata", {}).get("repo"),
            "plan_started": data.get("plan_started"),
            "apply_started": data.get("apply_started"),
            "last_sync_time": data.get("last_sync_time")
        })

    total = len(summaries)
    failures = [s for s in summaries if s["status"] == "apply_failed"]
    approvals = [s for s in summaries if s["approval_required"]]
    unsynced = [s for s in summaries if s["sync_status"] == "failed"]

    return {
        "total_runs": total,
        "failed_runs": len(failures),
        "approval_required": len(approvals),
        "port_sync_failures": len(unsynced),
        "recent_runs": sorted(summaries, key=lambda x: x.get("plan_started") or "", reverse=True)[:5]
    }


@app.post("/blueprints/{blueprint_id}/approve")
async def approve_blueprint(blueprint_id: str, _: None = Depends(verify_token)):
    record_path = f"{DB_PATH}/{blueprint_id}.json"
    if not os.path.exists(record_path):
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    with open(record_path) as f:
        record = json.load(f)
    record["status"] = "approved"
    with open(record_path, "w") as f:
        json.dump(record, f, indent=2)

    return {"blueprint_id": blueprint_id, "status": "approved"}

@app.post("/blueprints/{blueprint_id}/apply")
async def apply_blueprint(blueprint_id: str, _: None = Depends(verify_token)):
    record_path = f"{DB_PATH}/{blueprint_id}.json"
    if not os.path.exists(record_path):
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    with open(record_path) as f:
        record = json.load(f)
    record["status"] = "applied"
    record["applied_at"] = datetime.utcnow().isoformat()
    with open(record_path, "w") as f:
        json.dump(record, f, indent=2)

    return {"blueprint_id": blueprint_id, "status": "applied"}
