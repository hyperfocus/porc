# Port Integration with PORC and Terraform Enterprise

This document describes how the Port developer portal integrates with the PORC orchestrator to provide infrastructure visibility, blueprint cataloging, and run-time status tracking.

---
# Key Concepts
# 1. Blueprint Catalog (Design-Time)

Port maintains a list of **available blueprints** defined and approved by the platform team.

- **Entity kind**: `blueprint_template`
- Synced from GitHub or internal registry
- Represents a reusable Terraform module with metadata
# Example Blueprint Template Entity

```json
{
  "identifier": "gke-cluster-1-0-0",
  "title": "GKE Cluster Blueprint v1.0.0",
  "properties": {
    "module_path": "gke-cluster/1.0.0",
    "repo_url": "https://github.com/hyperfocus/infra-modules/gke-cluster",
    "inputs_required": ["region", "project_id"],
    "owner": "cloud-platform",
    "status": "active"
  }
}
```

---
# 2. Blueprint Instances (Run-Time)

Every time a blueprint is rendered, planned, or applied by PORC, a **blueprint_instance** entity is created or updated in Port.

- **Entity kind**: `blueprint_instance`
- Linked to blueprint_template
- Updated by PORC during `submit`, `plan`, `apply`
# Example Blueprint Instance Entity

```json
{
  "identifier": "gke-dev-west",
  "title": "GKE Dev Cluster (West)",
  "properties": {
    "workspace_id": "ws-abc123",
    "terraform_status": "applied",
    "run_id": "run-456def",
    "blueprint": "gke-cluster-1-0-0",
    "region": "us-west1",
    "repo_url": "https://github.com/hyperfocus/porc-blueprints/gke",
    "tfe_link": "https://tfe.td.com/app/td-platform/workspaces/ws-abc123/runs/run-456def"
  }
}
```

---
# Execution Flow

| PORC Event    | Port Update                     |
|---------------|----------------------------------|
| `pine submit` | Create or update `blueprint_instance` |
| `pine build`  | Update metadata (inputs, region, repo) |
| `pine plan`   | Set `terraform_status = planned` |
| `pine apply`  | Set `terraform_status = applied` |

---
# Port API Reference

To create or update an entity:

```
POST /v1/entities
Authorization: Bearer <PORT_API_TOKEN>
Content-Type: application/json
```

To update status:

```json
{
  "identifier": "gke-dev-west",
  "properties": {
    "terraform_status": "applied",
    "run_id": "run-789ghi"
  }
}
```

---
# Optional: Define Actions in Port

Port supports actions like "Re-run plan", "Apply now" — these can trigger PORC endpoints, e.g.:

```
POST /runs/{run_id}/apply
Authorization: Bearer <token>
```

Use this to expose PORC-triggered workflows in the Port UI while keeping source of truth in PORC.

---
# Summary

- PORC remains the executor and validator
- Port is the live registry for both blueprint definitions and deployed infra
- No blueprint creation flows through Port
- Status is passively updated via API by PORC

---
# Notes on Integration

Port/Backstage should consume data via:

- `GET /run/{run_id}/summary` — structured metadata for display
- `GET /run/{run_id}/status` — optional polling