![PORC Logo](https://github.com/hyperfocus/porc/raw/main/logo.png)

# PORC + PINE: Terraform Blueprint Orchestration Platform

**PORC (Platform Orchestrator)** and **PINE (Platform Infrastructure Entrypoint)** work together to validate, render, and manage Terraform blueprints across a secure, policy-enforced deployment pipeline.

---

## Components

### PINE (CLI)
PINE is a lightweight CLI used by developers to interact with the orchestration system.

**Local-only commands:**
- `pine lint <file>` — Schema structure check
- `pine validate <file>` — Blueprint spec validation

**Remote/PORC-integrated commands:**
- `pine submit <blueprint.json>` — Submit blueprint, receive `run_id`
- `pine build --run-id <id>` — Render & upload Terraform package
- `pine plan --run-id <id>` — Trigger plan via TFE
- `pine apply --run-id <id>` — Trigger apply via TFE

---

### PORC (FastAPI Orchestrator)
PORC receives validated blueprints, renders Terraform code, and interfaces with **Terraform Enterprise** to execute runs.

**Key Endpoints:**
- `POST /blueprint`
- `POST /runs/{run_id}/build`
- `POST /runs/{run_id}/plan`
- `POST /runs/{run_id}/apply`

PORC enforces:
- Schema + spec validation
- Sentinel policy checks via TFE
- Auth via `Authorization: Bearer <token>`

---

## Terraform Integration

- Remote runs handled via **Terraform Enterprise API**
- Configurations uploaded via `configuration-versions`
- Policies enforced by Sentinel

---

## Docs and References

See the `/docs` folder for:
- [PINE Usage Guide](docs/PINE%20Usage%20Guide.md)
- [PINE CLI Reference](docs/PINE%20CLI%20Reference.md)
- [Architecture](docs/Architecture.md)
- [API Reference](docs/API.md)
- [Development Status](docs/Development%20Status.md)