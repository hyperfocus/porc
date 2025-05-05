import requests
import os
import json

TFE_TOKEN = os.getenv("TFE_TOKEN")
TFE_ORG = "td-organization"
TFE_HOST = "https://app.terraform.io/api/v2"

headers = {
    "Authorization": f"Bearer {TFE_TOKEN}",
    "Content-Type": "application/vnd.api+json"
}

def get_workspace_id(workspace_name):
    url = f"{TFE_HOST}/organizations/{TFE_ORG}/workspaces/{workspace_name}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch workspace: {r.text}")
    return r.json()["data"]["id"]

def create_config_version(workspace_id):
    url = f"{TFE_HOST}/workspaces/{workspace_id}/configuration-versions"
    payload = {
        "data": {
            "type": "configuration-versions",
            "attributes": {"auto-queue-runs": False}
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["data"]["id"], r.json()["data"]["attributes"]["upload-url"]

def upload_files(upload_url, archive_path):
    with open(archive_path, "rb") as f:
        headers_upload = {"Content-Type": "application/octet-stream"}
        r = requests.put(upload_url, data=f, headers=headers_upload)
        r.raise_for_status()

def trigger_plan_run(workspace_id, config_id):
    url = f"{TFE_HOST}/runs"
    payload = {
        "data": {
            "attributes": {"is-destroy": False, "message": "PORC Plan"},
            "type": "runs",
            "relationships": {
                "workspace": {"data": {"type": "workspaces", "id": workspace_id}},
                "configuration-version": {"data": {"type": "configuration-versions", "id": config_id}}
            }
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["data"]["id"]


def upload_tarball(upload_url, directory):
    import tarfile
    import tempfile

    tar_path = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz").name

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(directory, arcname=".")

    with open(tar_path, "rb") as f:
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.put(upload_url, headers=headers, data=f)
        if response.status_code != 200:
            raise Exception(f"Failed to upload configuration: {response.text}")

def create_run(workspace_id, config_version_id, auto_apply=False):
    url = f"{TFE_HOST}/runs"
    payload = {
        "data": {
            "attributes": {
                "auto-apply": auto_apply,
                "is-destroy": False
            },
            "type": "runs",
            "relationships": {
                "workspace": {
                    "data": {"type": "workspaces", "id": workspace_id}
                },
                "configuration-version": {
                    "data": {"type": "configuration-versions", "id": config_version_id}
                }
            }
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 201:
        raise Exception(f"Failed to create run: {r.text}")
    return r.json()
