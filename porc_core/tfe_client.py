"""
TFE Client: Handles communication with Terraform Enterprise API.
"""
import requests
import time
import logging
import sys
import json
import base64
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
        token = token or get_tfe_token()
        # Decode base64 token if it looks like base64
        try:
            if '.' in token and len(token) % 4 == 0:
                decoded_token = base64.b64decode(token).decode('utf-8')
                self.token = decoded_token
            else:
                self.token = token
        except Exception as e:
            logging.warning(f"Failed to decode token as base64, using as-is: {e}")
            self.token = token
            
        # Ensure API URL has https scheme
        self.api_url = api_url or get_tfe_api()
        self.org = org or get_tfe_org()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.api+json"
        }
        self.timeout = 10  # seconds
        self.max_retries = 3
        self.retry_delay = 2

    def _request_with_retries(self, method, url, **kwargs):
        """Helper to perform HTTP requests with retries and timeout."""
        # Ensure URL has https scheme if it's a relative path
        if not url.startswith('http'):
            url = f"{self.api_url}/{url.lstrip('/')}"
            
        for attempt in range(self.max_retries):
            try:
                response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
                return response
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
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