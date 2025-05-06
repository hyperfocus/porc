# Sentinel Policy Enforcement in PORC

This document describes how Terraform Sentinel policies are enforced in the PORC orchestration pipeline.

---
# Purpose

Sentinel is used to enforce security, compliance, and operational policies across all Terraform runs initiated by PORC.

---
# Enforcement Scope

Sentinel is applied in **Terraform Enterprise** (TFE) using:

- **Remote backends**
- **Remote workspaces**
- **Enforced policy sets** attached to workspaces by tags or org

PORC ensures every plan/apply goes through TFE where policies are evaluated automatically.

---
# Policy Execution Flow

1. **PINE** lints and renders the blueprint.
2. **PORC build** generates `.tf` and `.tfvars.json`.
3. **PORC plan** uploads the config to TFE.
4. **TFE evaluates Sentinel policies**:
   - Before plan or apply executes
   - If policies fail, run is blocked

---
# PORC Behavior

PORC never bypasses Sentinel.

- If Sentinel fails a plan, the run stays in a `policy_failed` state.
- No apply is triggered.
- Users must update the blueprint or module inputs to satisfy the policies.

---
# Policy Location

Policies are **not stored in PORC**.

- They are managed centrally in TFE.
- Policy sets are assigned via Terraform Cloud/TFE configuration.

---
# Future Enhancements

- Expose Sentinel evaluation output via `/report/{run_id}`
- Include policy compliance in metrics
- Optionally validate policies via a dry-run TFE org before submitting