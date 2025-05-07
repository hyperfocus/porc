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
from porc_common.config import DB_PATH, RUNS_PATH
from porc_core.render import render_blueprint
from motor.motor_asyncio import AsyncIOMotorClient
from porc_core.tfe_client import TFEClient
from porc_common.errors import TFEServiceError
from enum import Enum

# Environment configuration
class Environment(str, Enum):
    DEV = "dev"
    PAT = "pat"
    PROD = "prod"

# Terraform Cloud configuration
TFE_HOST = os.getenv("TFE_HOST", "app.terraform.io")
TFE_ORG = os.getenv("TFE_ORG", "porc_test")  # Default to porc_test organization
TFE_ENV = os.getenv("TFE_ENV", Environment.DEV.value)
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "")

def sanitize_workspace_name(name: str) -> str:
    """Convert repository name to valid workspace name."""
    # Replace invalid characters with hyphens
    name = re.sub(r'[^a-zA-Z0-9\-_]', '-', name)
    # Ensure it starts with a letter or number
    if not name[0].isalnum():
        name = 'ws-' + name
    return name.lower()

def get_workspace_name() -> str:
    """Generate workspace name based on GitHub repository and environment."""
    if not TFE_ORG:
        raise ValueError("TFE_ORG environment variable is not set")
    
    if not GITHUB_REPOSITORY:
        raise ValueError("GITHUB_REPOSITORY environment variable is not set")
    
    # Validate environment
    try:
        env = Environment(TFE_ENV)
    except ValueError:
        raise ValueError(f"Invalid environment: {TFE_ENV}. Must be one of: {[e.value for e in Environment]}")
    
    # Extract repository name (remove owner prefix if present)
    repo_name = GITHUB_REPOSITORY.split('/')[-1]
    
    # Format: repo-name-env
    workspace_name = f"{sanitize_workspace_name(repo_name)}-{env.value}"
    return workspace_name

def ensure_workspace_exists(tfe: TFEClient, workspace_name: str) -> str:
    """Ensure workspace exists, create if it doesn't."""
    try:
        workspace_id = tfe.get_workspace_id(workspace_name)
        return workspace_id
    except TFEServiceError as e:
        if "not found" in str(e).lower():
            logging.info(f"Creating workspace: {workspace_name}")
            return tfe.create_workspace(
                name=workspace_name,
                organization=TFE_ORG,
                auto_apply=True,  # Auto-apply for dev environment
                execution_mode="remote"
            )
        raise

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

@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    from fastapi.responses import JSONResponse
    logging.info("Health check endpoint called")
    response = JSONResponse(content={"status": "ok"})
    logging.info(f"Health check response: {response.body}")
    return response

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

@app.post("/run/{run_id}/plan")
async def plan_run(run_id: str):
    """Run 'terraform plan' for the given run_id using Terraform Cloud."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(run_dir):
        return JSONResponse(status_code=404, content={"error": "Run files not found"})
    
    try:
        # Get workspace name based on GitHub repository and environment
        workspace_name = get_workspace_name()
        
        # Initialize TFE client with configuration
        tfe = TFEClient(
            host=TFE_HOST,
            organization=TFE_ORG
        )
        
        # Ensure workspace exists
        workspace_id = ensure_workspace_exists(tfe, workspace_name)
        
        # Create a new configuration version
        config_version_id, upload_url = tfe.create_config_version(workspace_id)
        
        # Create a zip of the terraform files
        import zipfile
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                for root, _, files in os.walk(run_dir):
                    for file in files:
                        if file.endswith('.tf'):
                            zf.write(os.path.join(root, file), 
                                   os.path.relpath(os.path.join(root, file), run_dir))
        
        # Upload the configuration
        tfe.upload_files(upload_url, tmp.name)
        os.unlink(tmp.name)  # Clean up temp file
        
        # Create and start a run
        tfe_run_id = tfe.create_run(workspace_id, config_version_id)
        
        # Wait for the run to complete
        status = tfe.wait_for_run(tfe_run_id)
        
        # Get the plan output
        plan_output = tfe.get_plan_output(tfe_run_id)
        
        # Save the output
        with open(f"{run_dir}/plan.out", "w") as f:
            f.write(plan_output)
        
        return {
            "run_id": run_id,
            "tfe_run_id": tfe_run_id,
            "workspace": workspace_name,
            "status": "planned" if status == "planned_and_finished" else "plan_failed",
            "output": plan_output[:TRUNCATE_OUTPUT]
        }
    except ValueError as e:
        error_msg = str(e)
        logging.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={"error": error_msg}
        )
    except TFEServiceError as e:
        error_msg = f"Terraform Cloud error: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )
    except Exception as e:
        error_msg = f"Error running terraform plan: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@app.post("/run/{run_id}/apply")
async def apply_run(run_id: str):
    """Run 'terraform apply' for the given run_id using Terraform Cloud."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    run_dir = f"{RUNS_PATH}/{run_id}"
    if not os.path.exists(run_dir):
        return JSONResponse(status_code=404, content={"error": "Run files not found"})
    
    try:
        # Get workspace name based on GitHub repository and environment
        workspace_name = get_workspace_name()
        
        # Initialize TFE client with configuration
        tfe = TFEClient(
            host=TFE_HOST,
            organization=TFE_ORG
        )
        
        # Ensure workspace exists
        workspace_id = ensure_workspace_exists(tfe, workspace_name)
        
        # Apply the run
        tfe.apply_run(run_id)
        
        # Wait for the apply to complete
        status = tfe.wait_for_run(run_id)
        
        # Get the apply output
        apply_output = tfe.get_apply_output(run_id)
        
        # Save the output
        with open(f"{run_dir}/apply.out", "w") as f:
            f.write(apply_output)
        
        return {
            "run_id": run_id,
            "tfe_run_id": run_id,
            "workspace": workspace_name,
            "status": "applied" if status == "applied" else "apply_failed",
            "output": apply_output[:TRUNCATE_OUTPUT]
        }
    except ValueError as e:
        error_msg = str(e)
        logging.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={"error": error_msg}
        )
    except TFEServiceError as e:
        error_msg = f"Terraform Cloud error: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )
    except Exception as e:
        error_msg = f"Error running terraform apply: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

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
