"""
Pine CLI: Blueprint linter and schema validator for PORC.
"""
import json
import sys
import os
import logging
from pathlib import Path

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'name': record.name,
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

SCHEMA_DIR = Path(os.getenv("PINE_SCHEMA_DIR", Path(__file__).parent / "schemas"))

class BlueprintValidationError(Exception):
    """Raised when blueprint validation fails."""
    pass

def lint(blueprint_path):
    """Lint a blueprint file for required fields and schema existence."""
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    errors = []
    if "kind" not in blueprint:
        errors.append("Missing 'kind' in blueprint")
    if "schema_version" not in blueprint:
        errors.append("Missing 'schema_version' in blueprint")

    if errors:
        logging.error("Validation failed:")
        for err in errors:
            logging.error(f"- {err}")
        raise BlueprintValidationError(errors)

    schema_path = (SCHEMA_DIR 
        / blueprint["kind"] 
        / f"{blueprint['schema_version']}.json")
    if not schema_path.exists():
        logging.error(f"Schema not found: {schema_path}")
        raise BlueprintValidationError([f"Schema not found: {schema_path}"])

    # TODO: Add JSON Schema validation here
    logging.info(f"Blueprint schema path is valid: {schema_path}")

def healthz():
    """Health check for the pine CLI process."""
    print(json.dumps({"status": "ok"}))
    sys.exit(0)

if __name__ == "__main__":
    """Entry point for the pine CLI."""
    if len(sys.argv) > 1 and sys.argv[1] == "healthz":
        healthz()
    if len(sys.argv) != 3 or sys.argv[1] != "lint":
        print("Usage: python pine/main.py lint <blueprint.json>")
        sys.exit(1)
    try:
        lint(sys.argv[2])
    except BlueprintValidationError as e:
        sys.exit(1)