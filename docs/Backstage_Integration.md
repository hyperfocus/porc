# Backstage Integration with Terraform Enterprise and PORC

This document outlines how Backstage can integrate with Terraform Enterprise (TFE) and PORC to provide infrastructure status visibility to developers without directly exposing blueprint logic.

---
# Concepts
# 1. **Infrastructure Blueprint Catalog (Optional)**
Backstage can optionally display a catalog of reusable infrastructure blueprints (paved paths) managed by the platform team. These represent Terraform template repositories, e.g.:

- `gke-cluster-blueprint`
- `rds-postgres-blueprint`

This catalog is for **discovery only** and is separate from service deployment status.

---
# 2. **Service-Centric Infra Status (Recommended Integration)**

Each service in Backstage (e.g., `payments-api`) can be annotated with its Terraform workspace:

```yaml
metadata:
  annotations:
    terraform.io/workspace-id: ws-abc1234567890
    terraform.io/organization: td-platform
```

The [GlobalLogic Terraform Plugin](https://github.com/GlobalLogic/backstage-plugins/tree/main/plugins/terraform) uses these annotations to:

- Query Terraform Enterprise
- Display the last run status (planned, applied, errored)
- Link directly to the TFE UI

No blueprint information is required for this.

---
# Execution Flow

- All Terraform actions (submit, build, plan, apply) still flow through `PINE` and `PORC`
- Backstage is **read-only** and does not trigger Terraform runs
- Status data is pulled from the TFE API using workspace annotations

---
# Benefits

- Developers get visibility into infrastructure state
- Platform team retains full control over execution via PORC
- No coupling between Backstage and blueprint structure

---
# Optional: Blueprint Discovery

If desired, blueprints themselves can be registered as Backstage components with:

```yaml
kind: Component
metadata:
  name: gke-cluster-blueprint
  annotations:
    terraform.io/template: true
```

This enables discovery but does not affect runtime execution.

---
# Notes on Integration

Port/Backstage should consume data via:

- `GET /run/{run_id}/summary` — structured metadata for display
- `GET /run/{run_id}/status` — optional polling