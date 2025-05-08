import os

def get_env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

# Only fetch secrets from the environment when needed, not at import time

def get_tfe_token():
    return get_env("TFE_TOKEN", required=True)

def get_tfe_api():
    return get_env("TFE_API", default="https://app.terraform.io/api/v2")

def get_tfe_org():
    return get_env("TFE_ORG", default="porc_test")

def get_tfe_env():
    return get_env("TFE_ENV", default="dev")

def get_github_repository():
    return get_env("GITHUB_REPOSITORY", default="")

def get_storage_account():
    return get_env("STORAGE_ACCOUNT")

def get_storage_access_key():
    return get_env("STORAGE_ACCESS_KEY")

def get_storage_bucket():
    return get_env("STORAGE_BUCKET", default="porcbundles")

def get_github_app_id():
    return get_env("GITHUB_APP_ID", required=True)

def get_github_app_installation_id():
    return get_env("GITHUB_APP_INSTALLATION_ID", required=True)

def get_github_app_private_key():
    return get_env("GITHUB_APP_PRIVATE_KEY", required=True)

def get_github_app_type():
    return get_env("GITHUB_APP_TYPE", default="app")

# Use hardcoded defaults for runtime paths
DB_PATH = "/tmp/porc-metadata"
RUNS_PATH = "/tmp/porc-runs"
AUDIT_PATH = "/tmp/porc-audit"

for path in [DB_PATH, RUNS_PATH, AUDIT_PATH]:
    os.makedirs(path, exist_ok=True)