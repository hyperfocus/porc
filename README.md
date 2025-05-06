# PORC (Platform Orchestrator)

PORC is a centralized orchestrator for Terraform blueprints, designed to automate lifecycle execution across teams via GitOps or API control.

## Key Components

- **API (`porc_api`)** – FastAPI endpoints to submit, render, plan, and apply blueprints
- **Worker (`porc_worker`)** – Polls and monitors run status or events
- **CLI (`pine`)** – Optional tool for validating blueprints offline
- **Core (`porc_core`)** – Encapsulates logic for rendering and Terraform Enterprise (TFE) integration
- **Common (`porc_common`)** – Shared config and error handling

## API Endpoints

See: [API Docs](api.md) or visit `/docs` after launching the server

## Deployment

Run in AKS via:

```bash
docker run -e TFE_TOKEN=xxx -p 8000:8000 porc:latest api
```

Or launch the worker:

```bash
docker run -e TFE_TOKEN=xxx porc:latest worker
```

## Flowchart

See [flowchart.mmd](flowchart.mmd) for lifecycle visual.