![PORC Logo](https://github.com/hyperfocus/porc/raw/main/logo.png)

# PORC (Platform Orchestrator)

PORC is a centralized Terraform orchestrator designed to standardize blueprint submission, validation, rendering, and execution across teams.

## Features

- CLI-driven lifecycle via PINE (`submit`, `build`, `plan`, `apply`)
- Remote Terraform Enterprise (TFE) execution
- Run metadata tracking and status reporting
- Audit logging (per run)
- External integration points for:
  - Backstage (status-only)
  - Port (catalog + status)

## Documentation

- [Backstage Integration](docs/Backstage_Integration.md)
- [Port Integration](docs/Port_Integration.md)

## Audit & Observability

Each run is logged to `/tmp/porc-audit/{run_id}.log`, including:
- Submit, build, plan, apply actions
- Timestamps and metadata
- Placeholders for:
  - DataDog telemetry
  - Dynatrace event reporting

## Folder Structure

```
porc_api/
  main.py
  porc_audit.py
  ...
docs/
  Backstage_Integration.md
  Port_Integration.md
```

## Status Endpoints

- `GET /run/{run_id}/status` - lightweight polling status
- `GET /run/{run_id}/summary` - full metadata for UI integrations

## Audit & Metrics

PORC automatically logs:

- **Audit events**: submit, build, plan, apply
- **Per-run audit logs**: `/tmp/porc-audit/{run_id}.log`
- **Delivery metrics**: captured on `apply` into `/tmp/porc-metrics.jsonl`
- Timestamps, blueprint metadata, workspace ID, and duration

These support downstream observability and trend analysis.

## Helm Deployment

See `DEPLOYMENT.md` for Kubernetes-based installation with external MongoDB support.
