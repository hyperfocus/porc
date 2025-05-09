# PORC System Architecture

This document describes the architecture of the PORC platform orchestrator and how its components interact.

---

## Overview

PORC consists of:

- **PINE CLI**: Developer tool for linting and rendering Terraform files from blueprints
- **PORC API**: FastAPI backend for managing runs, uploads, and Terraform orchestration
- **Port**: Blueprint source and reporting interface
- **Terraform Enterprise**: Execution engine with Sentinel enforcement
- **GitHub**: CI/CD workflow trigger and feedback loop

---

## Configuration

### Environment Variables

Required environment variables:
- `TFE_TOKEN`: Terraform Cloud API token
- `TFE_API`: Terraform Cloud API URL (default: https://app.terraform.io/api/v2)
- `TFE_ORG`: Terraform Cloud organization name
- `TFE_ENV`: Environment name (e.g., dev, prod)
- `MONGO_URI`: MongoDB connection string
- `GITHUB_REPOSITORY`: GitHub repository name
- `STORAGE_ACCOUNT`: Azure Storage account name
- `STORAGE_ACCESS_KEY`: Azure Storage account access key
- `STORAGE_BUCKET`: Azure Blob container name (default: porcbundles)

### Terraform Enterprise Integration

The PORC API communicates with Terraform Enterprise using:
- API URL: Configured via `TFE_API` environment variable
- Authentication: Bearer token via `TFE_TOKEN`
- Organization: Specified by `TFE_ORG`
- Workspace naming: `{org}-{env}` (e.g., `porc_test-dev`)

### Azure Blob Storage Integration

The PORC API uses Azure Blob Storage for:
- Storing deployment bundles (rendered Terraform files)
- Retrieving bundles for plan and apply operations
- Container name: `porcbundles` (configurable via `STORAGE_BUCKET`)
- Authentication: Storage account name and access key

---

## Mermaid Flow Diagram (Corrected)

```mermaid
flowchart LR
  A[Developer] --> B[GitHub Repo]
  B --> C[Port Blueprint]
  C --> D{Webhook or Kafka}

  D -->|GitHub Action| E[PORC API]
  D -->|Kafka Message| E

  E --> F[PINE: Lint + Submit Blueprint to Port]
  E --> G[Build + Plan + Apply to Terraform Cloud]
  E --> H[Sync Status to Port]

  G --> I[Sentinel Policy Enforcement]
  G --> J[Terraform Apply]

  E --> K[Logs + Metadata Store]
  K --> L[Reports, Metrics, Callbacks]
  
  E --> M[Azure Blob Storage]
  M -->|Store| N[Deployment Bundles]
  M -->|Retrieve| O[Terraform Files]
```

```
Developer --> GitHub Repo --> Port Blueprint --> [Kafka or Webhook]
                                                  |
                                                  v
                                         +------------------+
                                         |      PORC API     |
                                         +------------------+
                                           |        |       |
                          /lint & render <-+        +-> /notify (Port)
                          |                        /plan + /apply (TFE)
                      +--------+                +----------------+
                      |  PINE  |<---------------+  Mongo/FS Store |
                      +--------+                +----------------+
```

---

## Key Flows

### Blueprint Ingestion
- Blueprint submitted from GitHub or Port
- Stored locally by PORC and assigned a `run_id`

### Rendering
- PINE is used to validate blueprint schema and submit it to Port
- Output files: `main.tf`, `terraform.tfvars.json`
- Files are bundled and stored in Azure Blob Storage

### Execution
- PORC retrieves deployment bundle from Azure Blob Storage
- Pushes files to Terraform Enterprise using remote workspaces
- Sentinel enforces policy before apply

### Reporting
- Status synced back to Port via Terraform provider
- GitHub Check Runs posted using commit SHA
- Logs written locally and exposed via `/logs` and `/report`

---

## Persistence and State

- Metadata: `/tmp/porc-metadata/{run_id}.json`
- Deployment Bundles: Azure Blob Storage container `porcbundles`
- Logs: `/tmp/porc-logs/{run_id}.log.jsonl`

---

## Future Enhancements

- Replace FS with MongoDB or Postgres
- Replace Kafka/Webhooks with unified pub/sub event layer
- Add UI for reviewing plan/apply output and history

### Client–Server Design

- **PINE CLI**: Local developer interface (submit, build, plan, apply)
- **PORC API**: Validates blueprints, renders Terraform, interacts with TFE
- **TFE**: Executes plan and apply runs, enforces Sentinel policies
