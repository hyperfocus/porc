
import json
from pathlib import Path
import sys
import os
import requests

import argparse

SCHEMA_DIR = Path(__file__).parent / "schemas"

def lint(blueprint_path):
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    errors = []
    if "kind" not in blueprint:
        errors.append("Missing 'kind' in blueprint")
    if "schema_version" not in blueprint:
        errors.append("Missing 'schema_version' in blueprint")

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

def validate(path):
    print(f"Running extended validation for {path}... (stub)")

def build(path):
    print(f"Triggering remote render for {path}... (stub)")

def get_headers():
    token = os.getenv("PORC_TOKEN")
    if not token:
        print("Error: PORC_TOKEN environment variable not set")
        sys.exit(1)
    return {"Authorization": f"Bearer {token}"}

def submit(path):
    print(f"Submitting rendered blueprint from {path}...")
    headers = get_headers()
    # Simulated API call
    print(f"POST to /submit with headers {headers} (stub)")

def approve(blueprint_id):
    print(f"Approving blueprint ID {blueprint_id}...")
    headers = get_headers()
    # Simulated API call
    url = f"http://localhost:8000/blueprints/{blueprint_id}/approve"
    response = requests.post(url, headers=headers)
    print(response.json())

def apply(blueprint_id):
    print(f"Applying blueprint ID {blueprint_id}...")
    headers = get_headers()
    # Simulated API call
    url = f"http://localhost:8000/blueprints/{blueprint_id}/apply"
    response = requests.post(url, headers=headers)
    print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PINE CLI for blueprint management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("lint").add_argument("path")
    subparsers.add_parser("validate").add_argument("path")
    subparsers.add_parser("build").add_argument("path")
    subparsers.add_parser("submit").add_argument("path")
    subparsers.add_parser("approve").add_argument("blueprint_id")
    subparsers.add_parser("apply").add_argument("blueprint_id")

    args = parser.parse_args()

    if args.command == "lint":
        lint(args.path)
    elif args.command == "validate":
        validate(args.path)
    elif args.command == "build":
        build(args.path)
    elif args.command == "submit":
        submit(args.path)
    elif args.command == "approve":
        approve(args.blueprint_id)
    elif args.command == "apply":
        apply(args.blueprint_id)
