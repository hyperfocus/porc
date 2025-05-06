# PORC & PINE Development Status

This document tracks the current implementation status and outstanding items for the PINE CLI and PORC orchestrator.

---

## ✅ Fully Complete

### 1. CLI Commands (`pine`)
- `lint`, `validate` — Local-only validation
- `submit`, `build`, `plan`, `apply` — Fully implemented with PORC API integration
- Token-based auth (`PORC_TOKEN`)
- Routed using argparse

### 2. PORC API
- `POST /blueprint` — Accepts and validates blueprint
- `POST /runs/{run_id}/build` — Renders files, uploads to TFE
- `POST /runs/{run_id}/plan` — Initiates Terraform plan
- `POST /runs/{run_id}/apply` — Initiates Terraform apply
- Secured using `PORC_AUTH_TOKEN`

### 3. Terraform Integration
- Uses TFE Configuration Version API
- Creates run and uploads tarball
- Sentinel policies enforced by TFE
- Updated GitHub Actions: `terraform-plan.yml`, `terraform-apply.yml`

### 4. Documentation
- `PINE-CLI.md` (for wiki link)
- `PINE Usage Guide.md`
- `PINE CLI Reference.md`
- `API.md`, `Architecture.md`, `plan_apply_end_to_end.md`

---

## Future Enhancements (Optional)

| Feature | Description |
|---------|-------------|
| **Run status polling** | Monitor and report status of TFE runs |
| **Improved error reporting** | Propagate TFE errors (e.g., Sentinel failure) back to CLI |
| **GitHub Checks integration** | Report status to GitHub Checks API for automation feedback |
| **More blueprint types** | Extend support for kinds like `vpc`, `gke-nodepool`, etc. |
| **Audit/event logging** | Track PORC actions and API events per run_id |
| **UI or portal** | Optional UI wrapper for blueprint submission and review |

---

_Last updated: May 5, 2025_