# PINE Usage Guide

PINE is the developer-facing CLI tool for submitting and managing Terraform blueprints through the PORC orchestrator and Terraform Enterprise (TFE).
# When to Use PINE

Teams use PINE to:
- Submit infrastructure blueprints
- Trigger rendering and upload to TFE
- Plan and apply Terraform runs governed by Sentinel policies

PINE integrates with PORC, which owns the TFE interaction lifecycle.
# Blueprint Lifecycle

1. `pine submit <blueprint.json>` — Uploads and stages the blueprint
2. `pine build --run-id <id>` — Renders Terraform code and uploads to TFE
3. `pine plan --run-id <id>` — Triggers TFE `plan`
4. `pine apply --run-id <id>` — Triggers TFE `apply`

Sentinel policy enforcement occurs at the TFE layer. All operations must be approved and validated through PORC.
# Related Documentation

See [PINE CLI Reference](./PINE%20CLI%20Reference.md) for command syntax and examples.