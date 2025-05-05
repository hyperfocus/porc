# PINE CLI

Command-line interface for working with Terraform blueprints in the TD Delivery Platform.

---

### `pine lint <file>`

Validates the provided blueprint against the associated JSON schema.

**Input**:
- `<file>`: Path to the JSON blueprint (e.g., `examples/my-blueprint.json`)

**Returns**:
- Prints schema validation results
- Used for preflight checks and CI pipelines

---

### `pine validate <file>`

**Planned:** Performs extended validation of a blueprint beyond schema compliance.

**Input**:
- `<file>`: Path to the JSON blueprint file

**Planned Validation Scope**:
- Schema compliance
- Logical integrity (e.g., matching region + kind)
- Naming conventions and required metadata
- Service-specific rules (e.g., for GKE, PostgreSQL, etc.)
- Security and compliance guardrails

---

### `pine submit <file>`

Validates and submits a blueprint to the Port API to trigger the orchestration process.

**Input**:
- `<file>`: Path to the blueprint JSON

**Flags**:
- `--token <token>`: (Optional) API token for authenticating with Port
- `--env <env>`: (Optional) Environment identifier (e.g., `dev`, `prod`)
- `--external-id <id>`: (Optional) External run ID for traceability (e.g., GitHub Actions)

**Behavior**:
- Validates schema before sending
- Submits blueprint to Port via webhook
- Port routes to PORC for processing

---

### `pine build <file>`

**Planned:** Sends a validated blueprint to PORC for rendering Terraform configurations.

**Input**:
- `<file>`: Path to the blueprint JSON

**Flags**:
- `--dry-run`: (Optional) Validate and simulate rendering without committing

**Behavior**:
- Performs schema validation
- (Planned) Requests a preview render from PORC (no apply)

---

### New Commands

- `approve <blueprint_id>`: Approves a blueprint for apply.
- `apply <blueprint_id>`: Applies a previously approved blueprint.

### Authentication

All commands that interact with the PORC API must set the environment variable:

```bash
export PORC_TOKEN=<your-access-token>
```

This token is passed to the API as a Bearer token via Authorization headers.
