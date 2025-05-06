# PORC API Reference

This document describes the REST API endpoints exposed by the PORC orchestration service.

---
# Blueprint Handling
# `POST /blueprint`
Accepts a blueprint JSON, validates it, and saves it to local storage.

- **Input**: JSON blueprint (must contain `kind`, `schema_version`, and `metadata`)
- **Returns**: `{ "run_id": "porc-..." }`

---
# Build, Plan, Apply Workflow
# `POST /run/{run_id}/build`
Renders Terraform files from blueprint and stores to disk.

- **Returns**: `{ "status": "rendered", "files": [...] }`
# `POST /run/{run_id}/plan`
Packages rendered files, uploads to Terraform Enterprise, triggers `plan`.

- **Returns**: `{ "status": "plan_queued", "tfe_run_id": "..." }`
# `POST /run/{run_id}/apply`
Triggers `apply` for an existing plan (after approval if required).

- **Returns**: `{ "status": "apply_queued", "tfe_run_id": "..." }`

---
# Port Sync
# `POST /run/{run_id}/notify`
Generates a Terraform config that posts status back to Port via the Port provider.

- **Uses**: `port_entity` resource
- **Returns**: `{ "status": "port_sync_success" }` or error

---
# Run Metadata and Logs
# `GET /run/{run_id}/logs`
Returns an array of event log lines for a given run.
# `GET /metrics`
Returns summary statistics across all stored runs (success rates, duration averages, etc.)

---
# Reporting
# `GET /report/{run_id}`
Returns full metadata, blueprint, log lines, and rendered files for a single run.
# `GET /report/summary`
Returns a high-level rollup of recent run activity (last 5 runs, failure counts, etc.)

---
# Notes
- All data is persisted to local filesystem paths:
  - `/tmp/porc-metadata/`
  - `/tmp/porc-logs/`
  - `/tmp/porc-runs/`
- A remote Mongo or DB backend can be added later.
# New Endpoints (PORC)

- `POST /blueprint` — Accepts and stores validated blueprint, returns `run_id`
- `POST /runs/{run_id}/build` — Renders Terraform templates and uploads to TFE
- `POST /runs/{run_id}/plan` — Triggers Terraform Enterprise plan run
- `POST /runs/{run_id}/apply` — Triggers Terraform Enterprise apply run