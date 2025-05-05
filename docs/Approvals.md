# Approval and Change Control in PORC

PORC supports integration with enterprise change management systems like ServiceNow to enforce approval gates before infrastructure is applied.

---

## Overview

When a blueprint requires change control, PORC enforces it by:

1. Requiring a valid `change_record` ID.
2. Verifying its state before triggering `apply`.
3. Blocking execution unless the change is approved or an override is requested.

---

## Blueprint Flag

In the blueprint:

```json
"metadata": {
  "approval_required": true,
  "external_id": "github:org/repo@sha"
}
```

---

## Approval Metadata

After validation, PORC adds this to metadata:

```json
"approval": {
  "change_record": "CHG123456",
  "validated": true,
  "override": false
}
```

---

## Validation Process

- PORC queries the ServiceNow API for the change ID.
- It ensures the record is in an `implement` or `scheduled` state.
- If not valid, `apply` is blocked unless manually overridden.

---

## Override Logic

If an override is requested:

- The approval block is bypassed
- PORC marks the run with `"override": true`
- This is tracked in logs and reports for audit

---

## Future Features

- Audit log export to SIEM
- Emergency change workflow
- Team-specific approval rules

## Approval Flow

Blueprints must be approved before they can be applied.

- Use `pine approve <blueprint_id>` to mark a blueprint as approved.
- The PORC API enforces bearer token authentication.
- The `PORC_TOKEN` must be provided as an environment variable to authenticate.

See `API.md` and `PINE-CLI.md` for full details.
