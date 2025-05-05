import json
from pathlib import Path
import sys

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