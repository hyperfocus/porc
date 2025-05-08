import os

def get_env(name, required=False):
    value = os.getenv(name)
    if required and not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

# Remove all top-level required secrets
# Instead, provide functions to fetch them when needed

def get_tfe_token():
    return get_env("TFE_TOKEN", required=True)

def get_tfe_api():
    return get_env("TFE_API", required=False) or "https://app.terraform.io/api/v2"

def get_tfe_org():
    return get_env("TFE_ORG", required=False) or "porc_test"

def get_tfe_env():
    return get_env("TFE_ENV", required=False) or "dev"

def get_github_repository():
    return get_env("GITHUB_REPOSITORY", required=False) or ""

def get_storage_account():
    return get_env("STORAGE_ACCOUNT", required=False)

def get_storage_access_key():
    return get_env("STORAGE_ACCESS_KEY", required=False)

def get_storage_bucket():
    return get_env("STORAGE_BUCKET", required=False) or "porcbundles"

# Any other config values should be accessed via a function, not at import time.

# Runtime paths
DB_PATH = get_env("PORC_DB_PATH", "/tmp/porc-metadata")
RUNS_PATH = get_env("PORC_RUNS_PATH", "/tmp/porc-runs")
AUDIT_PATH = get_env("PORC_AUDIT_PATH", "/tmp/porc-audit")

for path in [DB_PATH, RUNS_PATH, AUDIT_PATH]:
    os.makedirs(path, exist_ok=True)