# PORC: Platform Orchestrator

**PORC** (Platform Orchestrator) is an internal service designed to orchestrate infrastructure provisioning through Terraform Enterprise using blueprints submitted by developers, Port, or GitHub workflows.

## Repo Structure

| Folder        | Description                            |
|---------------|----------------------------------------|
| `porc_core`   | Shared business logic for blueprint validation, state, and rendering |
| `porc_api`    | FastAPI web service for blueprint ingest, approval, and plan/apply orchestration |
| `porc_worker` | Kafka or webhook-based background consumer (optional) |
| `pine`        | CLI for local blueprint validation and linting |
| `schemas`     | Blueprint input and metadata schema contracts |
| `tests`       | Unit tests for each major component |

## Getting Started

```bash
# Run the API (FastAPI)
uvicorn porc_api.main:app --reload

# Run the CLI (PINE)
python pine/main.py validate examples/my-blueprint.json
```

## Features

- JSON schema + metadata validation
- Secret redaction
- GitHub and Port ID traceability
- TFE workspace and Sentinel policy enforcement
- CLI and API alignment

