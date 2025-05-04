# PINE CLI Reference

PINE (PORC Infrastructure Negotiation Engine) is the command-line tool for validating and rendering blueprints before they are handed off to PORC.

---

## Commands

### `pine lint <file>`
Validates the input blueprint JSON against the schema registry.

- **Input**: Path to blueprint JSON file
- **Returns**: Success or schema validation errors

#### Example
```bash
pine lint examples/my-blueprint.json
```

---

### `pine render <file> --out <directory>`
Renders Terraform configuration (`main.tf`, `terraform.tfvars.json`) from blueprint.

- **Input**: Path to blueprint file
- **Flags**:
  - `--out`: Output directory for rendered `.tf` files
- **Returns**: Renders files to specified directory

#### Example
```bash
pine render examples/gke-blueprint.json --out ./rendered/gke/
```

---

### `pine validate <file>`
(Planned) Blueprint validation beyond schema — e.g., logical integrity, naming, service-specific rules.

---

## Blueprint Format

Blueprints must include:
- `kind`: Resource type (e.g., `gke-cluster`)
- `schema_version`: Matching schema in registry
- `metadata`: Additional config (e.g., `repo`, `external_id`, `approval_required`)
- `variables`: Key-value pairs to render

---

## Folder Structure

Schemas are stored in:

```
pine/schemas/{kind}/{schema_version}.json
```

Blueprints must match a schema to pass linting.

---

## Exit Codes

- `0`: Success
- `1`: Validation or rendering failure