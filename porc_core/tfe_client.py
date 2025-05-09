"""
TFE Client: Handles communication with Terraform Enterprise API.
"""
import requests
import time
import logging
import sys
import json
from typing import Dict, Any, Optional
from porc_common.config import get_tfe_token, get_tfe_api, get_tfe_org
from porc_common.errors import TFEServiceError

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

class TFEClient:
    """Client for interacting with the Terraform Enterprise (TFE) API."""
    def __init__(self, token=None, api_url=None, org=None):
        """Initialize the TFEClient with authentication and API details."""
        self.token = token or get_tfe_token()
        if not self.token:
            raise ValueError("TFE_TOKEN environment variable is not set")
            
        self.api_url = api_url or get_tfe_api()
        if not self.api_url:
            raise ValueError("TFE_API environment variable is not set")
            
        self.org = org or get_tfe_org()
        if not self.org:
            raise ValueError("TFE_ORG environment variable is not set")
            
        logging.info(f"Initializing TFE client for org: {self.org}, API: {self.api_url}")
        
        # Validate token format
        if not self.token.startswith(('at-', 'tk-')):
            logging.warning("TFE token does not start with expected prefix (at- or tk-)")
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.api+json"
        }
        self.timeout = 10  # seconds
        self.max_retries = 3
        self.retry_delay = 2

    def _log_request_details(self, method: str, url: str, headers: Dict[str, str], **kwargs) -> None:
        """Log request details with sensitive information redacted."""
        # Create a copy of headers and redact sensitive information
        safe_headers = headers.copy()
        if 'Authorization' in safe_headers:
            auth_parts = safe_headers['Authorization'].split()
            if len(auth_parts) == 2:
                token = auth_parts[1]
                safe_headers['Authorization'] = f"{auth_parts[0]} {token[:4]}...{token[-4:]}"
            else:
                safe_headers['Authorization'] = '[REDACTED]'

        logging.info(f"Making request: {method} {url}")
        logging.debug(f"Headers: {json.dumps(safe_headers, indent=2)}")
        if 'json' in kwargs:
            logging.debug(f"Request body: {json.dumps(kwargs['json'], indent=2)}")

    def _log_response_details(self, response: requests.Response) -> None:
        """Log response details."""
        logging.info(f"Response status: {response.status_code}")
        logging.debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        try:
            body = response.json()
            if response.status_code >= 400:
                logging.error(f"Error response body: {json.dumps(body, indent=2)}")
            else:
                logging.debug(f"Response body: {json.dumps(body, indent=2)}")
        except ValueError:
            logging.debug(f"Response text: {response.text}")

    def _request_with_retries(self, method: str, url: str, **kwargs) -> requests.Response:
        """Helper to perform HTTP requests with retries, timeout, and logging."""
        # Ensure URL has https scheme if it's a relative path
        if not url.startswith('http'):
            url = f"{self.api_url}/{url.lstrip('/')}"

        self._log_request_details(method, url, self.headers, **kwargs)

        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
                self._log_response_details(response)

                if response.status_code == 401:
                    raise TFEServiceError(response.status_code, 
                        "Authentication failed. Please check your TFE_TOKEN is valid and has correct permissions.")
                elif response.status_code == 403:
                    raise TFEServiceError(response.status_code,
                        "Authorization failed. Your token does not have permission to perform this action.")
                elif response.status_code == 404:
                    error_msg = f"Resource not found: {url}"
                    try:
                        error_data = response.json()
                        if 'errors' in error_data:
                            error_details = json.dumps(error_data['errors'], indent=2)
                            error_msg += f"\nError details:\n{error_details}"
                    except ValueError:
                        error_msg += f"\nResponse text: {response.text}"
                    raise TFEServiceError(response.status_code, error_msg)
                elif response.status_code >= 400:
                    error_msg = f"TFE API Error ({response.status_code}): {url}"
                    try:
                        error_data = response.json()
                        if 'errors' in error_data:
                            error_details = json.dumps(error_data['errors'], indent=2)
                            error_msg += f"\nError details:\n{error_details}"
                    except ValueError:
                        error_msg += f"\nResponse text: {response.text}"
                    raise TFEServiceError(response.status_code, error_msg)

                return response
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logging.warning(f"Request attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"Request to {url} failed after {self.max_retries} attempts: {e}")
                    raise TFEServiceError(-1, f"Request to {url} failed after {self.max_retries} attempts: {e}")

    def get_workspace_id(self, name):
        """Get the workspace ID for a given workspace name."""
        url = f"{self.api_url}/organizations/{self.org}/workspaces/{name}"
        r = self._request_with_retries("GET", url)
        if r.status_code != 200:
            logging.error(f"Failed to get workspace ID for {name}: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        data = r.json()
        if "data" not in data or "id" not in data["data"]:
            logging.error(f"Malformed response from {url}: {data}")
            raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
        return data["data"]["id"]

    def create_config_version(self, workspace_id):
        """Create a new configuration version for a workspace."""
        url = f"{self.api_url}/workspaces/{workspace_id}/configuration-versions"
        payload = {
            "data": {
                "type": "configuration-versions",
                "attributes": {"auto-queue-runs": False}
            }
        }
        r = self._request_with_retries("POST", url, json=payload)
        if r.status_code != 201:
            logging.error(f"Failed to create config version for workspace {workspace_id}: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        data = r.json()
        if "data" not in data or "id" not in data["data"] or "attributes" not in data["data"] or "upload-url" not in data["data"]["attributes"]:
            logging.error(f"Malformed response from {url}: {data}")
            raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
        return data["data"]["id"], data["data"]["attributes"]["upload-url"]

    def upload_files(self, upload_url, archive_path):
        """Upload configuration files to the given upload URL."""
        with open(archive_path, "rb") as f:
            r = requests.put(upload_url, data=f.read(), headers={"Content-Type": "application/octet-stream"}, timeout=self.timeout)
        if r.status_code != 200:
            logging.error(f"Failed to upload files to {upload_url}: {r.text}")
            raise TFEServiceError(r.status_code, f"{upload_url}: {r.text}")

    def create_workspace(self, name, org, auto_apply=False, execution_mode="remote"):
        """Create a new workspace in the organization."""
        url = f"{self.api_url}/organizations/{org}/workspaces"
        payload = {
            "data": {
                "type": "workspaces",
                "attributes": {
                    "name": name,
                    "auto-apply": auto_apply,
                    "execution-mode": execution_mode
                }
            }
        }
        r = self._request_with_retries("POST", url, json=payload)
        if r.status_code != 201:
            logging.error(f"Failed to create workspace {name}: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        data = r.json()
        if "data" not in data or "id" not in data["data"]:
            logging.error(f"Malformed response from {url}: {data}")
            raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
        return data["data"]["id"]

    def create_run(self, workspace_id, config_version_id):
        """Create a new run in the workspace."""
        url = f"{self.api_url}/runs"
        payload = {
            "data": {
                "type": "runs",
                "attributes": {
                    "auto-apply": True
                },
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id
                        }
                    },
                    "configuration-version": {
                        "data": {
                            "type": "configuration-versions",
                            "id": config_version_id
                        }
                    }
                }
            }
        }
        r = self._request_with_retries("POST", url, json=payload)
        if r.status_code != 201:
            logging.error(f"Failed to create run: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        data = r.json()
        if "data" not in data or "id" not in data["data"]:
            logging.error(f"Malformed response from {url}: {data}")
            raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
        return data["data"]["id"]

    def create_plan(self, workspace_id, bundle_url):
        """Create a new plan using a configuration bundle URL."""
        # First create a new configuration version
        config_version_id, upload_url = self.create_config_version(workspace_id)
        
        # Download the bundle and upload it to TFE
        r = requests.get(bundle_url, timeout=self.timeout)
        if r.status_code != 200:
            raise TFEServiceError(r.status_code, f"Failed to download bundle from {bundle_url}")
        
        # Upload the configuration
        headers = {"Content-Type": "application/octet-stream"}
        r = requests.put(upload_url, data=r.content, headers=headers, timeout=self.timeout)
        if r.status_code != 200:
            raise TFEServiceError(r.status_code, f"Failed to upload configuration to {upload_url}")
        
        # Create and return the run ID
        return self.create_run(workspace_id, config_version_id)

    def wait_for_run(self, run_id):
        """Wait for a run to complete and return its final status."""
        url = f"{self.api_url}/runs/{run_id}"
        while True:
            r = self._request_with_retries("GET", url)
            if r.status_code != 200:
                logging.error(f"Failed to get run status: {r.text}")
                raise TFEServiceError(r.status_code, f"{url}: {r.text}")
            data = r.json()
            if "data" not in data or "attributes" not in data["data"] or "status" not in data["data"]["attributes"]:
                logging.error(f"Malformed response from {url}: {data}")
                raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
            status = data["data"]["attributes"]["status"]
            if status in ["planned_and_finished", "applied", "errored", "canceled", "discarded"]:
                return status
            time.sleep(5)  # Wait 5 seconds before checking again

    def get_plan_output(self, run_id):
        """Get the plan output for a run."""
        url = f"{self.api_url}/runs/{run_id}/plan"
        r = self._request_with_retries("GET", url)
        if r.status_code != 200:
            logging.error(f"Failed to get plan output: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        data = r.json()
        if "data" not in data or "attributes" not in data["data"] or "log-read-url" not in data["data"]["attributes"]:
            logging.error(f"Malformed response from {url}: {data}")
            raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
        log_url = data["data"]["attributes"]["log-read-url"]
        r = requests.get(log_url, timeout=self.timeout)
        if r.status_code != 200:
            logging.error(f"Failed to get plan log: {r.text}")
            raise TFEServiceError(r.status_code, f"{log_url}: {r.text}")
        return r.text

    def get_apply_output(self, run_id):
        """Get the apply output for a run."""
        url = f"{self.api_url}/runs/{run_id}/apply"
        r = self._request_with_retries("GET", url)
        if r.status_code != 200:
            logging.error(f"Failed to get apply output: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        data = r.json()
        if "data" not in data or "attributes" not in data["data"] or "log-read-url" not in data["data"]["attributes"]:
            logging.error(f"Malformed response from {url}: {data}")
            raise TFEServiceError(r.status_code, f"Malformed response from {url}: {data}")
        log_url = data["data"]["attributes"]["log-read-url"]
        r = requests.get(log_url, timeout=self.timeout)
        if r.status_code != 200:
            logging.error(f"Failed to get apply log: {r.text}")
            raise TFEServiceError(r.status_code, f"{log_url}: {r.text}")
        return r.text

    def apply_run(self, run_id):
        """Apply a run that has been planned."""
        url = f"{self.api_url}/runs/{run_id}/actions/apply"
        r = self._request_with_retries("POST", url)
        if r.status_code != 202:
            logging.error(f"Failed to apply run: {r.text}")
            raise TFEServiceError(r.status_code, f"{url}: {r.text}")
        return True