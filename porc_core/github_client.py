"""
PORC Core GitHub: Client for interacting with GitHub Checks API.
"""
import os
import logging
import aiohttp
import jwt
import time
from typing import Dict, Any, Optional

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token or GitHub App credentials."""
        self._token = token
        self._headers = None
        self._app_id = os.getenv("GITHUB_APP_ID")
        self._installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
        self._private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
        self._app_type = os.getenv("GITHUB_APP_TYPE", "pat")
        self._session = None
    
    @property
    async def session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    @property
    def token(self) -> str:
        """Get the GitHub token, initializing it if needed."""
        if self._token is None:
            if self._app_type == "app":
                # Generate JWT for GitHub App
                now = int(time.time())
                payload = {
                    'iat': now,
                    'exp': now + 300,  # 5 minutes
                    'iss': self._app_id
                }
                jwt_token = jwt.encode(payload, self._private_key, algorithm='RS256')
                
                # Get installation access token
                headers = {
                    'Authorization': f'Bearer {jwt_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                response = requests.post(
                    f'https://api.github.com/app/installations/{self._installation_id}/access_tokens',
                    headers=headers
                )
                response.raise_for_status()
                self._token = response.json()['token']
            else:
                # Use PAT
                self._token = os.getenv("GITHUB_TOKEN")
                if not self._token:
                    raise ValueError("GitHub token is required")
        return self._token
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get the request headers, initializing them if needed."""
        if self._headers is None:
            if self._app_type == "app":
                self._headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            else:
                self._headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
        return self._headers
    
    async def create_check_run(self, owner: str, repo: str, sha: str, name: str) -> Dict[str, Any]:
        """Create a new check run."""
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
        data = {
            "name": name,
            "head_sha": sha,
            "status": "in_progress"
        }
        session = await self.session
        async with session.post(url, headers=self.headers, json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def update_check_run(self, owner: str, repo: str, check_run_id: int, 
                        status: str, conclusion: Optional[str] = None,
                        output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing check run."""
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs/{check_run_id}"
        data = {
            "status": status,
            "conclusion": conclusion,
            "output": output
        }
        session = await self.session
        async with session.patch(url, headers=self.headers, json=data) as response:
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