import json
from pathlib import Path
import sys
import requests

SCHEMA_DIR = Path(__file__).parent / "schemas"


def lint(blueprint_path):
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    errors = []
    if "kind" not in blueprint:
        errors.append("Missing 'kind' in blueprint")
    if "schema_version" not in blueprint:
        errors.append("Missing schema_version in blueprint")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    schema_path = SCHEMA_DIR / blueprint["kind"] / f"{blueprint['schema_version']}.json"
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        sys.exit(1)

    print("Blueprint schema path is valid:", schema_path)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "lint":
        print("Usage: python pine/main.py lint <blueprint.json>")
        sys.exit(1)
    lint(sys.argv[2])


def validate(blueprint_path):
    print("[validate] Starting extended blueprint validation...")
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    findings = []
    if "metadata" not in blueprint:
        findings.append("Missing 'metadata' block.")

    if "kind" in blueprint and not blueprint["kind"].startswith("gke-"):
        findings.append("Only 'gke-' prefixed kinds are currently allowed.")

    if findings:
        print("Validation findings:")
        for issue in findings:
            print(f"- {issue}")
        sys.exit(1)

    print("Extended validation passed.")


def build(blueprint_path):
    print("[build] Validating and submitting blueprint for render preview...")
    validate(blueprint_path)
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    response = requests.post("https://porc.internal/api/v1/build", json=blueprint)
    if response.status_code == 200:
        print("Preview render request submitted successfully.")
        print("Response:", response.json())
    else:
        print("Build failed:", response.status_code, response.text)
        sys.exit(1)
