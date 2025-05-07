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
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token is required")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
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

# Initialize the GitHub client
github_client = GitHubClient() 