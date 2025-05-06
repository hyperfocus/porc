# Port Integration via Terraform Provider

PORC supports syncing run metadata and status back to [Port](https://www.getport.io/) using the official Port Terraform provider.

---

## Purpose

Syncing to Port allows:
- Centralized visibility of infrastructure changes
- Blueprint-to-run traceability
- Integration with Port scorecards, insights, and dashboards

---

## Provider Configuration

PORC auto-generates the following Terraform file during sync:

```hcl
provider "port" {}

resource "port_entity" "porc_run" {
  identifier = var.identifier
  title      = "PORC Run ${var.identifier}"
  blueprint  = "porc_run"

  properties = {
    status        = var.status
    started_at    = var.started_at
    finished_at   = var.finished_at
    external_id   = var.external_id
    change_record = var.change_record
  }
}
```

### Variables

These are injected from `port_notify.tfvars.json`:

```json
{
  "identifier": "porc-20250505-123456",
  "status": "apply_complete",
  "started_at": "2025-05-05T12:34:56Z",
  "finished_at": "2025-05-05T12:38:00Z",
  "external_id": "github:org/repo@sha",
  "change_record": "CHG12345"
}
```

---

## Run Flow

1. Run is executed and recorded in PORC
2. PORC builds and applies a Terraform configuration that posts the status to Port
3. Result is logged and stored for audit

---

## Requirements

- Port blueprint called `porc_run` must exist
- `PORT_CLIENT_ID` and `PORT_CLIENT_SECRET` must be set in environment

---

## Future Improvements

- Support delta updates or patching Port entities
- Link run to blueprint automatically using relations
- Use Port SDK or GraphQL API instead of TF provider