import os

def get_env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and value is None:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

# Example config usage
TFE_TOKEN = get_env("TFE_TOKEN", required=True)
TFE_HOST = get_env("TFE_HOST", "https://app.terraform.io/api/v2")
TFE_ORG = get_env("TFE_ORG", "td-organization")

# Runtime paths
DB_PATH = get_env("PORC_DB_PATH", "/tmp/porc-metadata")
RUNS_PATH = get_env("PORC_RUNS_PATH", "/tmp/porc-runs")
AUDIT_PATH = get_env("PORC_AUDIT_PATH", "/tmp/porc-audit")

for path in [DB_PATH, RUNS_PATH, AUDIT_PATH]:
    os.makedirs(path, exist_ok=True)