"""
PORC Core GitHub: Client for interacting with GitHub Checks API.
"""
import os
import logging
import requests
from typing import Dict, Any, Optional

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token."""
        self._token = token
        self._headers = None
    
    @property
    def token(self) -> str:
        """Get the GitHub token, initializing it if needed."""
        if self._token is None:
            self._token = os.getenv("GITHUB_TOKEN")
            if not self._token:
                raise ValueError("GitHub token is required")
        return self._token
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get the request headers, initializing them if needed."""
        if self._headers is None:
            self._headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
        return self._headers
    
    def create_check_run(self, owner: str, repo: str, sha: str, name: str) -> Dict[str, Any]:
        """Create a new check run."""
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
        data = {
            "name": name,
            "head_sha": sha,
            "status": "in_progress"
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_check_run(self, owner: str, repo: str, check_run_id: int, 
                        status: str, conclusion: Optional[str] = None,
                        output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing check run."""
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs/{check_run_id}"
        data = {
            "status": status,
            "conclusion": conclusion,
            "output": output
        }
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

def get_github_client() -> GitHubClient:
    """Get a GitHub client instance."""
    return GitHubClient()

# Initialize the GitHub client
github_client = get_github_client() 