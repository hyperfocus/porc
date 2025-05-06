import requests
from porc_common.config import TFE_TOKEN, TFE_HOST, TFE_ORG
from porc_common.errors import TFEServiceError

class TFEClient:


    def __init__(self, token=TFE_TOKEN, host=TFE_HOST, org=TFE_ORG):

        self.token = token
        self.host = host
        self.org = org
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.api+json"
        }

    def get_workspace_id(self, name):

        url = f"{self.host}/organizations/{self.org}/workspaces/{name}"
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:

            raise TFEServiceError(r.status_code, r.text)
        return r.json()["data"]["id"]

    def create_config_version(self, workspace_id):

        url = f"{self.host}/workspaces/{workspace_id}/configuration-versions"
        payload = {
            "data": {
                "type": "configuration-versions",
                "attributes": {"auto-queue-runs": False}
            }
        }
        r = requests.post(url, headers=self.headers, json=payload)
        if r.status_code != 201:

            raise TFEServiceError(r.status_code, r.text)
        return r.json()["data"]["id"], r.json()["data"]["attributes"]["upload-url"]

    def upload_files(self, upload_url, archive_path):

        with open(archive_path, "rb") as f:

            r = requests.put(upload_url, data=f.read(), headers={"Content-Type": "application/octet-stream"})
        if r.status_code != 200:

            raise TFEServiceError(r.status_code, r.text)
