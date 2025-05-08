"""
PORC Core GitHub: Client for interacting with GitHub Checks API.
"""
import os
import logging
import aiohttp
import jwt
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from porc_common.config import (
    get_github_app_id,
    get_github_app_installation_id,
    get_github_app_private_key,
    get_github_app_type
)

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token or GitHub App credentials."""
        self._token = token
        self._headers = None
        self._app_id = get_github_app_id()
        self._installation_id = get_github_app_installation_id()
        self._private_key = get_github_app_private_key()
        self._app_type = get_github_app_type()
        self._session = None
    
    @property
    async def session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    @property
    async def token(self) -> str:
        """Get the GitHub token, initializing it if needed."""
        if self._token is None:
            logging.info(f"Initializing GitHub token with app_type={self._app_type}")
            if self._app_type == "app":
                # Generate JWT for GitHub App
                now = int(time.time())
                payload = {
                    'iat': now,
                    'exp': now + 300,  # 5 minutes
                    'iss': self._app_id
                }
                logging.info(f"Generating JWT for GitHub App ID {self._app_id}")
                jwt_token = jwt.encode(payload, self._private_key, algorithm='RS256')
                
                # Get installation access token
                headers = {
                    'Authorization': f'Bearer {jwt_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                session = await self.session
                logging.info(f"Getting installation access token for installation {self._installation_id}")
                async with session.post(
                    f'https://api.github.com/app/installations/{self._installation_id}/access_tokens',
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    self._token = (await response.json())['token']
                    logging.info("Successfully obtained installation access token")
            else:
                # Use PAT
                self._token = os.getenv("GITHUB_TOKEN")
                if not self._token:
                    logging.error("GitHub token is required but not set")
                    raise ValueError("GitHub token is required")
                logging.info("Using GitHub PAT token")
        return self._token
    
    @property
    async def headers(self) -> Dict[str, str]:
        """Get the request headers, initializing them if needed."""
        if self._headers is None:
            token = await self.token
            if self._app_type == "app":
                self._headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                logging.info("Using GitHub App authentication headers")
            else:
                self._headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                logging.info("Using GitHub PAT authentication headers")
        return self._headers
    
    async def create_check_run(self, owner: str, repo: str, sha: str, name: str) -> Dict[str, Any]:
        """Create a new check run."""
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
        # Extract run_id from name (format: "PORC Plan - {run_id}" or "PORC Terraform Apply")
        run_id = name.split(" - ")[-1] if " - " in name else "unknown"
        data = {
            "name": name,
            "head_sha": sha,
            "status": "in_progress",
            "started_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "output": {
                "title": name,
                "summary": f"Starting check run for run_id: {run_id}"
            }
        }
        session = await self.session
        headers = await self.headers
        logging.info("=== GitHub Check Run API Request ===")
        logging.info(f"Method: POST")
        logging.info(f"URL: {url}")
        logging.info(f"Headers: {json.dumps(headers, indent=2)}")
        logging.info(f"Request Body: {json.dumps(data, indent=2)}")
        async with session.post(url, headers=headers, json=data) as response:
            response_text = await response.text()
            logging.info(f"Response Status: {response.status}")
            logging.info(f"Response Body: {response_text}")
            if response.status != 201:
                logging.error(f"Failed to create check run: {response_text}")
                raise Exception(f"Failed to create check run: {response_text}")
            result = json.loads(response_text)
            logging.info(f"Successfully created check run: {json.dumps(result, indent=2)}")
            return result
    
    async def update_check_run(self, owner: str, repo: str, check_run_id: int, 
                        status: str, conclusion: Optional[str] = None,
                        output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing check run."""
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs/{check_run_id}"
        
        # Extract run_id from output title if available
        run_id = "unknown"
        if output and "title" in output:
            title_parts = output["title"].split(" - ")
            if len(title_parts) > 1:
                run_id = title_parts[-1]
        
        # Add run_id to summary if not already present
        if output and "summary" in output and "run_id" not in output["summary"].lower():
            output["summary"] = f"Run ID: {run_id}\n{output['summary']}"
        
        data = {
            "status": status,
            "conclusion": conclusion,
            "output": output
        }
        session = await self.session
        headers = await self.headers
        async with session.patch(url, headers=headers, json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

def get_github_client() -> GitHubClient:
    """Get a GitHub client instance."""
    return GitHubClient()

# Initialize the GitHub client
github_client = get_github_client() 