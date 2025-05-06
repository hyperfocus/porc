# PINE CLI Reference

This document provides detailed instructions for using the `pine` CLI.

## Setup

Install the CLI and set the following environment variable:

```bash
export PORC_TOKEN=<your-api-token>
```

## Commands

### Local-only commands

- `pine lint <file>` — Basic schema validation (kind + schema_version)
- `pine validate <file>` — Extended validation using blueprint schema

### PORC-integrated commands

- `pine submit <blueprint.json>`  
  Uploads blueprint and returns `run_id`.

- `pine build --run-id <id>`  
  Tells PORC to render and upload Terraform templates to TFE.

- `pine plan --run-id <id>`  
  Triggers a TFE plan.

- `pine apply --run-id <id>`  
  Triggers a TFE apply using the uploaded configuration.

## Example

```bash
pine submit my-blueprint.json
pine build --run-id porc-20250505-abc123
pine plan --run-id porc-20250505-abc123
pine apply --run-id porc-20250505-abc123
```

## See Also

- [PINE Usage Guide](./PINE%20Usage%20Guide.md)