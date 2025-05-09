# PORC Run Metadata Specification

This document outlines the structure and meaning of fields in the `run_id.json` files stored in `/tmp/porc-metadata`.

---

## Top-Level Fields

| Field            | Type     | Description |
|------------------|----------|-------------|
| `run_id`         | `string` | Unique ID assigned by PORC |
| `status`         | `string` | Run status (`submitted`, `rendered`, `plan_queued`, `apply_queued`, etc.) |
| `sync_status`    | `string` | Port sync result (`success`, `failed`) |
| `plan_started`   | `string` | ISO 8601 timestamp when plan began |
| `apply_started`  | `string` | ISO 8601 timestamp when apply began |
| `last_sync_time` | `string` | ISO 8601 timestamp when Port sync last occurred |

---

## Blueprint

The original user-submitted blueprint JSON. Common fields include:

| Field                | Type     | Description |
|----------------------|----------|-------------|
| `kind`               | `string` | Blueprint kind (e.g., `gke-cluster`) |
| `schema_version`     | `string` | Blueprint schema version |
| `metadata.repo`      | `string` | Repo used to name Terraform workspace |
| `metadata.external_id` | `string` | External reference (e.g., `github:owner/repo@sha`) |
| `metadata.approval_required` | `boolean` | If ServiceNow approval is required |

---

## Approval (Optional)

Present if `approval_required` is `true`.

| Field           | Type     | Description |
|-----------------|----------|-------------|
| `change_record` | `string` | ServiceNow Change ID |
| `validated`     | `bool`   | Was the change request verified? |
| `override`      | `bool`   | Was manual override used? |

---

## Example

```json
{
  "run_id": "porc-20250505-123456",
  "status": "apply_queued",
  "sync_status": "success",
  "plan_started": "2025-05-05T12:30:00Z",
  "apply_started": "2025-05-05T12:35:00Z",
  "last_sync_time": "2025-05-05T12:40:00Z",
  "blueprint": {
    "kind": "gke-cluster",
    "schema_version": "v1.2",
    "metadata": {
      "repo": "platform-gke",
      "external_id": "github:td/platform-gke@abc123",
      "approval_required": true
    }
  },
  "approval": {
    "change_record": "CHG123456",
    "validated": true,
    "override": false
  }
}
```