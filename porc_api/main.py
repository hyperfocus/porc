"""
PORC API: FastAPI service for blueprint submission, build, plan, apply, and status endpoints.
"""
import json
import os
import re
import logging
import sys
from datetime import datetime
from fastapi import FastAPI, Request, Path, Depends, APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from porc_common.config import DB_PATH, RUNS_PATH, get_tfe_api, get_tfe_org
from porc_core.render import render_blueprint
from motor.motor_asyncio import AsyncIOMotorClient
from porc_core.tfe_client import TFEClient
from porc_common.errors import TFEServiceError
from enum import Enum
import time
from porc_core.quill import quill_manager
from porc_core.github_client import GitHubClient, get_github_client
from porc_core.state import StateService, RunState, get_state_service
from porc_core.storage import StorageService, get_storage_service
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback
from typing import Optional

# Environment configuration
class Environment(str, Enum):
    DEV = "dev"
    PAT = "pat"
    PROD = "prod"

# Terraform Cloud configuration
TFE_ENV = os.getenv("TFE_ENV", Environment.DEV.value)

# Storage configuration
STORAGE_ACCOUNT = os.getenv("STORAGE_ACCOUNT")  # Azure storage account name
STORAGE_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY")  # Azure storage account access key
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "porcbundles")

# Initialize storage service with configuration
if not STORAGE_ACCOUNT or not STORAGE_ACCESS_KEY:
    logging.warning("Storage service not configured - missing required environment variables")

# Create FastAPI app
app = FastAPI(title="PORC API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
def get_storage_service_dependency() -> StorageService:
    return get_storage_service()

def get_github_client_dependency() -> GitHubClient:
    return get_github_client()

def get_state_service_dependency() -> StateService:
    return get_state_service()

def sanitize_workspace_name(name: str) -> str:
    """Convert repository name to valid workspace name."""
    # Replace invalid characters with hyphens
    name = re.sub(r'[^a-zA-Z0-9\-_]', '-', name)
    # Ensure it starts with a letter or number
    if not name[0].isalnum():
        name = 'ws-' + name
    return name.lower()

def get_workspace_name() -> str:
    """Generate workspace name based on environment."""
    if not get_tfe_org():
        raise ValueError("TFE_ORG environment variable is not set")
    
    # Validate environment
    try:
        env = Environment(TFE_ENV)
    except ValueError:
        raise ValueError(f"Invalid environment: {TFE_ENV}. Must be one of: {[e.value for e in Environment]}")
    
    # Format: porc-env
    return f"porc-{env.value}"

def ensure_workspace_exists(tfe: TFEClient, workspace_name: str) -> str:
    """Ensure workspace exists, create if it doesn't."""
    try:
        logging.info(f"Checking if workspace {workspace_name} exists")
        workspace_id = tfe.get_workspace_id(workspace_name)
        logging.info(f"Found existing workspace {workspace_name} with ID {workspace_id}")
        return workspace_id
    except TFEServiceError as e:
        if "not found" in str(e).lower():
            logging.info(f"Creating workspace: {workspace_name}")
            workspace_id = tfe.create_workspace(
                name=workspace_name,
                org=get_tfe_org(),
                auto_apply=True,  # Auto-apply for dev environment
                execution_mode="remote"
            )
            logging.info(f"Created new workspace {workspace_name} with ID {workspace_id}")
            return workspace_id
        logging.error(f"Failed to get/create workspace {workspace_name}: {str(e)}")
        raise

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
    external_reference: str  # e.g. GitHub PR reference
    source_repo: str  # The GitHub repository where the blueprint was submitted from

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
            "blueprint": payload.model_dump(mode='json'),
            "external_reference": payload.external_reference,
            "source_repo": payload.source_repo
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
async def build_from_blueprint(
    run_id: str = Path(...),
    storage_service: StorageService = Depends(get_storage_service_dependency),
    state_service: StateService = Depends(get_state_service_dependency)
):
    """Build files from a submitted blueprint for a given run_id."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    
    try:
        # Get the blueprint record
        meta_file = f"{DB_PATH}/{run_id}.json"
        if not os.path.exists(meta_file):
            return JSONResponse(status_code=404, content={"error": "Run ID not found"})
        
        with open(meta_file) as f:
            record = json.load(f)
        
        # Update state to BUILDING
        state_service.update_state(run_id, RunState.BUILDING)
        
        # Get blueprint details
        blueprint = record["blueprint"]
        kind = blueprint["kind"]
        variables = blueprint["variables"]
        
        try:
            # Render the QUILL template with blueprint variables
            files = quill_manager.render_quill(kind, variables)
            
            # Store the deployment bundle
            bundle_key = storage_service.store_deployment_bundle(run_id, files)
            
            # Generate bundle URL
            bundle_url = storage_service.get_bundle_url(bundle_key)
            
            # Update record with bundle key
            record["bundle_key"] = bundle_key
            record["status"] = "built"
            tmp_file = meta_file + ".tmp"
            with open(tmp_file, "w") as f:
                json.dump(record, f, indent=2)
            os.replace(tmp_file, meta_file)
            
            # Update state to BUILT
            state_service.update_state(
                run_id, 
                RunState.BUILT,
                metadata={
                    "bundle_key": bundle_key,
                    "bundle_url": bundle_url
                }
            )
            
            logging.info(f"Blueprint built: {run_id}")
            return {"run_id": run_id, "status": "built", "bundle_key": bundle_key, "bundle_url": bundle_url}
            
        except ValueError as e:
            # Update state to indicate build failure
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,  # Reuse plan_failed state for build failures
                metadata={"error": str(e)}
            )
            raise
            
    except ValueError as e:
        error_msg = str(e)
        logging.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={"error": error_msg}
        )
    except Exception as e:
        error_msg = f"Error building blueprint: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@app.post("/run/{run_id}/plan")
async def plan_run(
    run_id: str,
    storage_service: StorageService = Depends(get_storage_service_dependency),
    github_client: GitHubClient = Depends(get_github_client_dependency),
    state_service: StateService = Depends(get_state_service_dependency)
):
    """Run terraform plan and create/update GitHub check run."""
    try:
        # Get run state
        state = await state_service.get_state(run_id)
        if not state:
            return JSONResponse(status_code=404, content={"error": "Run not found"})
        
        # Verify state transition
        current_state = state.get("state")
        if current_state not in [RunState.BUILT.value, RunState.SUBMITTED.value]:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid state transition",
                    "details": f"Cannot plan from state '{current_state}'. Run must be in BUILT or SUBMITTED state."
                }
            )
        
        # Update state to PLANNING
        state_service.update_state(run_id, RunState.PLANNING)
        
        # Get the bundle URL from state
        metadata = state.get("metadata", {})
        bundle_url = metadata.get("bundle_url")
        if not bundle_url:
            # If bundle URL not in state, try to generate it from bundle key
            bundle_key = metadata.get("bundle_key")
            if not bundle_key:
                # This is a server error since the build step should have stored this
                state_service.update_state(
                    run_id,
                    RunState.PLAN_FAILED,
                    metadata={
                        "error": "Bundle key not found in state",
                        "error_type": "missing_bundle"
                    }
                )
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal error: Bundle key not found in state. The build step may have failed."}
                )
            try:
                bundle_url = storage_service.get_bundle_url(bundle_key)
                # Update state with bundle URL
                state_service.update_state(
                    run_id,
                    RunState.PLANNING,
                    metadata={**metadata, "bundle_url": bundle_url}
                )
            except ValueError as e:
                state_service.update_state(
                    run_id,
                    RunState.PLAN_FAILED,
                    metadata={
                        "error": str(e),
                        "error_type": "bundle_url_generation_failed"
                    }
                )
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Internal error: Failed to generate bundle URL: {str(e)}"}
                )
        
        # Get the blueprint record
        meta_file = f"{DB_PATH}/{run_id}.json"
        if not os.path.exists(meta_file):
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": "Blueprint record not found",
                    "error_type": "missing_blueprint"
                }
            )
            return JSONResponse(status_code=404, content={"error": "Run ID not found"})
        
        with open(meta_file) as f:
            record = json.load(f)
        
        # Get source repository from blueprint record
        source_repo = record.get("source_repo")
        if not source_repo:
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": "Source repository not found in blueprint",
                    "error_type": "missing_source_repo"
                }
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error: Source repository not found in blueprint"}
            )
        
        # Extract owner and repo from source_repo
        try:
            owner, repo = source_repo.split("/")
        except ValueError:
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": f"Invalid source repository format: {source_repo}",
                    "error_type": "invalid_source_repo"
                }
            )
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal error: Invalid source repository format: {source_repo}"}
            )
        
        # Get external reference (PR SHA) from blueprint record
        external_ref = record.get("external_reference")
        if not external_ref:
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": "External reference not found in blueprint",
                    "error_type": "missing_external_ref"
                }
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal error: External reference not found in blueprint"}
            )
        
        logging.info(f"Creating check run with SHA from blueprint: {external_ref}")
        
        # Create check run
        try:
            check_run = await github_client.create_check_run(
                owner=owner,
                repo=repo,
                sha=external_ref,
                name="PORC Plan",
                run_id=run_id
            )
        except Exception as e:
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": str(e),
                    "error_type": "github_check_creation_failed"
                }
            )
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to create GitHub check run: {str(e)}"}
            )
        
        try:
            # Run terraform plan
            tfe = TFEClient()
            workspace_name = get_workspace_name()
            logging.info(f"Getting/creating workspace: {workspace_name}")
            workspace_id = ensure_workspace_exists(tfe, workspace_name)
            logging.info(f"Using workspace {workspace_name} with ID: {workspace_id}")
            
            # Create plan
            logging.info(f"Creating plan in workspace {workspace_id} with bundle URL: {bundle_url}")
            plan_id = tfe.create_plan(workspace_id, bundle_url)
            logging.info(f"Created plan {plan_id} in workspace {workspace_id}")
            
            # Update check run with plan URL
            plan_url = f"https://app.terraform.io/app/{get_tfe_org()}/workspaces/{workspace_name}/runs/{plan_id}"
            logging.info(f"Plan URL: {plan_url}")
            await github_client.update_check_run(
                owner, repo, check_run["id"],
                status="completed",
                conclusion="success",
                output={
                    "title": "Plan Completed",
                    "summary": "Terraform plan completed successfully.",
                    "text": f"""## Run Details
**Run ID**: `{run_id}`
**Plan ID**: `{plan_id}`

## Plan Results
The plan has been created in Terraform Cloud. Click the URL below to view the detailed plan output.

Plan URL: {plan_url}"""
                }
            )
            
            # Update state
            state_service.update_state(
                run_id,
                RunState.PLANNED,
                metadata={
                    "plan_id": plan_id,
                    "plan_url": plan_url
                }
            )
            
            return {"status": "planned", "plan_id": plan_id, "plan_url": plan_url}
            
        except TFEServiceError as e:
            # Update check run with error
            error_details = {
                "title": "PORC Plan — Terraform Cloud Error",
                "summary": "Terraform plan failed due to a Terraform Cloud error. See details below.",
                "text": f"""```
Error connecting to Terraform Cloud:
- Organization: {get_tfe_org()}
- Workspace: {workspace_name}
- API Endpoint: {get_tfe_api()}
- Status Code: {getattr(e, 'status_code', 'Unknown')}
- Error Type: {e.__class__.__name__}

Full Error Message:
{str(e)}

Raw API Response:
{getattr(e, 'text', 'No response text available')}

Troubleshooting Steps:
1. Check that Terraform Cloud credentials are properly configured
2. Verify the workspace '{workspace_name}' exists in organization '{get_tfe_org()}'
3. Ensure the PORC service has the correct permissions
4. Check TFE token validity and permissions
5. Verify the organization name is correct in the configuration

For more details, check the logs or contact your administrator.
```"""
            }
            try:
                await github_client.update_check_run(
                    owner, repo, check_run["id"],
                    status="completed",
                    conclusion="failure",
                    output=error_details
                )
            finally:
                # Ensure client session is closed
                await github_client.close()
            
            # Update state to indicate plan failure
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": str(e),
                    "error_type": "terraform_cloud_error"
                }
            )
            
            return JSONResponse(
                status_code=500,
                content={"error": "Terraform Cloud error", "details": str(e)}
            )
            
        except Exception as e:
            # Update check run with error
            error_details = {
                "title": "PORC Plan — Error",
                "summary": "Terraform plan failed due to an unexpected error. See details below.",
                "text": f"""```
Error Details:
- Type: {e.__class__.__name__}
- Message: {str(e)}

Stack Trace:
{traceback.format_exc()}

For more details, check the logs or contact your administrator.
```"""
            }
            try:
                await github_client.update_check_run(
                    owner, repo, check_run["id"],
                    status="completed",
                    conclusion="failure",
                    output=error_details
                )
            finally:
                # Ensure client session is closed
                await github_client.close()
            
            # Update state to indicate plan failure
            state_service.update_state(
                run_id,
                RunState.PLAN_FAILED,
                metadata={
                    "error": str(e),
                    "error_type": "unexpected_error"
                }
            )
            
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to run plan", "details": str(e)}
            )
            
    except Exception as e:
        logging.error(f"Error running plan: {str(e)}", exc_info=True)
        # Ensure client session is closed in case of early exit
        if github_client:
            await github_client.close()
        
        # Update state to indicate plan failure
        state_service.update_state(
            run_id,
            RunState.PLAN_FAILED,
            metadata={
                "error": str(e),
                "error_type": "unexpected_error"
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to run plan", "details": str(e)}
        )

@app.post("/run/{run_id}/apply")
async def apply_run(
    run_id: str,
    storage_service: StorageService = Depends(get_storage_service_dependency),
    github_client: GitHubClient = Depends(get_github_client_dependency),
    state_service: StateService = Depends(get_state_service_dependency)
):
    """Run 'terraform apply' for the given run_id using Terraform Cloud."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    
    try:
        # Get the blueprint record
        meta_file = f"{DB_PATH}/{run_id}.json"
        if not os.path.exists(meta_file):
            return JSONResponse(status_code=404, content={"error": "Run ID not found"})
        
        with open(meta_file) as f:
            record = json.load(f)
        
        # Get current state
        current_state = await state_service.get_state(run_id)
        if not current_state or current_state.get("state") != RunState.PLANNED.value:
            return JSONResponse(
                status_code=400,
                content={"error": f"Run must be in PLANNED state, current state: {current_state.get('state') if current_state else 'unknown'}"}
            )
        
        # Extract GitHub info
        source_repo = record["source_repo"]
        external_ref = record["external_reference"]
        owner, repo = source_repo.split('/')
        
        # Create GitHub check run for apply
        check_run = await github_client.create_check_run(
            owner=owner,
            repo=repo,
            sha=external_ref,
            name="PORC Apply",
            run_id=run_id
        )
        check_run_id = check_run["id"]
        
        # Get workspace name based on GitHub repository and environment
        workspace_name = get_workspace_name()
        
        # Try to acquire workspace lock
        if not state_service.acquire_lock(workspace_name, run_id):
            return JSONResponse(
                status_code=409,
                content={"error": f"Workspace {workspace_name} is locked by another operation"}
            )
        
        try:
            # Update state to APPLYING
            state_service.update_state(
                run_id,
                RunState.APPLYING,
                workspace=workspace_name,
                metadata={"check_run_id": check_run_id}
            )
            
            # Initialize TFE client with configuration
            tfe = TFEClient(
                api_url=get_tfe_api(),
                org=get_tfe_org()
            )
            
            # Ensure workspace exists
            workspace_id = ensure_workspace_exists(tfe, workspace_name)
            
            # Create a new configuration version
            config_version_id, upload_url = tfe.create_config_version(workspace_id)
            
            # Get deployment bundle from storage
            bundle_key = record["bundle_key"]
            bundle = storage_service.get_deployment_bundle(bundle_key)
            
            # Upload the configuration
            tfe.upload_files(upload_url, bundle)
            
            # Wait for configuration version to be processed
            max_retries = 10
            retry_delay = 2
            for attempt in range(max_retries):
                try:
                    # Create and start a run
                    tfe_run_id = tfe.create_run(workspace_id, config_version_id)
                    break
                except TFEServiceError as e:
                    if "Configuration version is still being processed" in str(e) and attempt < max_retries - 1:
                        logging.info(f"Configuration version still processing, attempt {attempt + 1}/{max_retries}")
                        time.sleep(retry_delay)
                        continue
                    raise
            
            # Wait for the run to complete
            status = tfe.wait_for_run(tfe_run_id)
            
            # Get the apply output
            apply_output = tfe.get_apply_output(tfe_run_id)
            
            # Update GitHub check run for apply
            conclusion = "success" if status == "applied" else "failure"
            output = {
                "title": "Apply Complete",
                "summary": f"Terraform apply {conclusion}.",
                "text": f"""## Run Details
**Run ID**: `{run_id}`
**Status**: {status}

## Apply Output
```
{apply_output[:TRUNCATE_OUTPUT]}
```"""
            }
            await github_client.update_check_run(
                owner=owner,
                repo=repo,
                check_run_id=check_run_id,
                status="completed",
                conclusion=conclusion,
                output=output
            )
            
            # Update state based on apply result
            new_state = RunState.APPLIED if status == "applied" else RunState.APPLY_FAILED
            state_service.update_state(
                run_id,
                new_state,
                workspace=workspace_name,
                metadata={
                    "tfe_run_id": tfe_run_id,
                    "apply_output": apply_output[:TRUNCATE_OUTPUT]
                }
            )
            
            return {
                "run_id": run_id,
                "tfe_run_id": tfe_run_id,
                "workspace": workspace_name,
                "status": new_state.value,
                "output": apply_output[:TRUNCATE_OUTPUT]
            }
            
        finally:
            # Always release the workspace lock
            state_service.release_lock(workspace_name, run_id)
            
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
async def get_status(
    run_id: str,
    state_service: StateService = Depends(get_state_service_dependency)
):
    """Get the status of a run by run_id."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    
    try:
        # Get state from state service
        state = await state_service.get_state(run_id)
        if not state:
            return JSONResponse(status_code=404, content={"error": "Run ID not found"})
        
        # Get additional metadata from blueprint record
        meta_file = f"{DB_PATH}/{run_id}.json"
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                record = json.load(f)
                blueprint = record.get("blueprint", {})
                return {
                    "run_id": run_id,
                    "status": state["state"],
                    "workspace": state.get("workspace"),
                    "blueprint_kind": blueprint.get("kind"),
                    "external_reference": record.get("external_reference"),
                    "source_repo": record.get("source_repo"),
                    "metadata": state.get("metadata", {})
                }
        else:
            # If no metadata file exists, return just the state
            return {
                "run_id": run_id,
                "status": state["state"],
                "workspace": state.get("workspace"),
                "metadata": state.get("metadata", {})
            }
        
    except Exception as e:
        error_msg = f"Error getting run status: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

@app.get("/run/{run_id}/summary")
async def get_summary(
    run_id: str,
    storage_service: StorageService = Depends(get_storage_service_dependency),
    state_service: StateService = Depends(get_state_service_dependency)
):
    """Get a summary of a run, including status and file previews."""
    if sanitize_run_id(run_id):
        return sanitize_run_id(run_id)
    
    try:
        # Get state from state service
        state = await state_service.get_state(run_id)
        if not state:
            return JSONResponse(status_code=404, content={"error": "Run ID not found"})
        
        # Get blueprint record
        meta_file = f"{DB_PATH}/{run_id}.json"
        if not os.path.exists(meta_file):
            return JSONResponse(status_code=404, content={"error": "Run ID not found"})
        
        with open(meta_file) as f:
            record = json.load(f)
            blueprint = record.get("blueprint", {})
        
        # Get deployment bundle from storage if available
        files = {}
        if "bundle_key" in record:
            try:
                bundle = storage_service.get_deployment_bundle(record["bundle_key"])
                # Extract and read files from the bundle
                import zipfile
                import io
                with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
                    for fname in zf.namelist():
                        if fname.endswith('.tf'):
                            with zf.open(fname) as f:
                                files[fname] = f.read().decode('utf-8')[:1000]  # truncate file previews
            except Exception as e:
                logging.warning(f"Could not read deployment bundle: {str(e)}")
        
        return {
            "run_id": run_id,
            "status": state["state"],
            "workspace": state.get("workspace"),
            "blueprint_kind": blueprint.get("kind"),
            "external_reference": record.get("external_reference"),
            "source_repo": record.get("source_repo"),
            "metadata": state.get("metadata", {}),
            "files": files
        }
        
    except Exception as e:
        error_msg = f"Error getting run summary: {str(e)}"
        logging.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

quills_router = APIRouter()

@quills_router.post("/quills/")
async def upload_quill(
    kind: str = Form(...),
    version: str = Form("latest"),
    templates: UploadFile = File(...),
    schema: UploadFile = File(...)
):
    templates_data = await templates.read()
    schema_data = await schema.read()
    try:
        templates_json = json.loads(templates_data)
        schema_json = json.loads(schema_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    if mongo_db is not None:
        await mongo_db.quills.update_one(
            {"kind": kind, "version": version},
            {"$set": {"templates": templates_json, "schema": schema_json}},
            upsert=True
        )
    return {"status": "ok", "kind": kind, "version": version}

@quills_router.get("/quills/{kind}")
async def get_quill(kind: str, version: Optional[str] = "latest"):
    if mongo_db is None:
        raise HTTPException(status_code=500, detail="MongoDB not configured")
    quill = await mongo_db.quills.find_one({"kind": kind, "version": version})
    if not quill:
        raise HTTPException(status_code=404, detail="Quill not found")
    return {"templates": quill["templates"], "schema": quill["schema"]}

# Register the router
app.include_router(quills_router)
