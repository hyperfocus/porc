# Blueprint Security Validation (PINE)

PINE supports early-stage security checks on blueprints before they are submitted to Port or rendered by PORC. These checks enforce compliance, policy alignment, and platform contract rules.

---

## Purpose

Blueprint security validation ensures that infrastructure requests:
- Conform to platform expectations
- Include required metadata
- Avoid misconfiguration or risky defaults

---

## What PINE Validates

### 1. **Schema Validation**
- Checks `kind`, `schema_version`, and field presence
- Ensures blueprint matches the defined contract

### 2. **Custom Rule Checks**
These are loaded from rulesets (JSON or hardcoded logic) and include:

| Rule Type            | Example                              |
|---------------------|--------------------------------------|
| Required fields      | `approval_required`, `external_id`  |
| Restricted values    | Region must be `ca-central-1`       |
| Forbidden services   | Disallow `public_ip = true`         |
| Metadata enforcement | Require tags: `business_unit`, etc.|
| Naming patterns      | `repo` must match `[a-z0-9-]+`       |

---

## Example Rule (JSON)

```json
{
  "kind": "gke-cluster",
  "enforce": {
    "required": ["approval_required", "repo"],
    "pattern": {
      "repo": "^[a-z0-9-]+$"
    },
    "deny_values": {
      "region": ["us-east-1"]
    }
  }
}
```

---

## Future Enhancements

- Rule registry per `kind` or `platform`
- GitHub annotations for violations
- Severity levels (error, warning, info)
- Auto-fix suggestions for known issues

---

## Limitations

- **Does not scan Terraform**
- **Does not replace Sentinel**
- **Should be treated as a shift-left guardrail**