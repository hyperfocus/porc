import json
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent / "schemas"

def lint(blueprint_path):

    with open(blueprint_path) as f:
    pass
    # TODO: implement logic

        blueprint = json.load(f)

    errors = []
    if "kind" not in blueprint:

        errors.append("Missing 'kind' in blueprint")
    if "schema_version" not in blueprint:

        errors.append("Missing 'schema_version' in blueprint")

    if errors:

        print("Validation failed:")
        for err in errors:

            print("-", err)
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
