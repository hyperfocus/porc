import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_PAT")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def parse_external_id(external_id):
    # Format: github:owner/repo@sha
    if not external_id.startswith("github:"):
        return None
    try:
        _, repo_info = external_id.split("github:")
        repo_path, sha = repo_info.split("@")
        owner, repo = repo_path.split("/")
        return {"owner": owner, "repo": repo, "sha": sha}
    except Exception:
        return None

def post_check(run_id, external_id, check_name, conclusion, summary):
    info = parse_external_id(external_id)
    if not info:
        return {"error": "Invalid external_id"}

    url = f"https://api.github.com/repos/{info['owner']}/{info['repo']}/check-runs"
    payload = {
        "name": check_name,
        "head_sha": info["sha"],
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": f"{check_name} Result",
            "summary": summary
        }
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    return r.status_code, r.json()