
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
        self._token = token
        self._headers = None
        self._app_id = get_github_app_id()
        self._installation_id = get_github_app_installation_id()
        self._private_key = get_github_app_private_key()
        self._app_type = get_github_app_type()
        self._session = None

    @property
    async def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    @property
    async def token(self) -> str:
        if self._token is None:
            if self._app_type == "app":
                now = int(time.time())
                payload = {
                    'iat': now,
                    'exp': now + 300,
                    'iss': self._app_id
                }
                jwt_token = jwt.encode(payload, self._private_key, algorithm='RS256')
                headers = {
                    'Authorization': f'Bearer {jwt_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                session = await self.session
                async with session.post(
                    f'https://api.github.com/app/installations/{self._installation_id}/access_tokens',
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    self._token = (await response.json())['token']
            else:
                self._token = os.getenv("GITHUB_TOKEN")
                if not self._token:
                    raise ValueError("GitHub token is required")
        return self._token

    @property
    async def headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {await self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

    async def create_check_run(self, owner: str, repo: str, sha: str, name: str, details_url: str) -> int:
        data = {
            "name": name,
            "head_sha": sha,
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "details_url": details_url
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
        session = await self.session
        async with session.post(url, headers=await self.headers, json=data) as resp:
            resp.raise_for_status()
            result = await resp.json()
            return result["id"]

    async def update_check_run(self, owner: str, repo: str, check_run_id: int, conclusion: str, output: Dict[str, Any]) -> None:
        data = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "conclusion": conclusion,
            "output": output
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/check-runs/{check_run_id}"
        session = await self.session
        async with session.patch(url, headers=await self.headers, json=data) as resp:
            resp.raise_for_status()

    async def post_pr_comment(self, owner: str, repo: str, pr_number: int, comment: str) -> None:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        data = {"body": comment}
        session = await self.session
        async with session.post(url, headers=await self.headers, json=data) as resp:
            resp.raise_for_status()
            logging.info(f"Posted comment to PR #{pr_number}: {comment}")

def get_github_client() -> GitHubClient:
    return GitHubClient()
