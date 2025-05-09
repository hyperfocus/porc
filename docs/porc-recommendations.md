# PORC: Strategic Recommendations

These improvements are focused on evolving PORC into a best-in-class Terraform orchestration and paved-path platform for TD Bank.

---

## 1. Double Down on Platform-as-a-Service UX

- **Current strength**: GitHub + PINE CLI integration for paved path consumption.
- **Recommended improvements**:
  - Add `porc summary` to provide:
    - Visual overview of the module graph
    - Blueprint variables
    - Linked Sentinel policy results
  - Auto-post GitHub PR annotations with:
    - Plan summary
    - Module and dependency tree
    - Drift or diff insights
  - Add `pine init <template>` to bootstrap blueprint overlays from a pre-defined catalog
  - Generate pre-filled GitHub Actions workflows based on blueprint metadata

---

## 2. Policy Extensibility

- **Current**: Sentinel enforced only through TFE.
- **Recommended improvements**:
  - Support for **pre-run policy plugins** (e.g. validate JSON schemas, tag enforcement, disallowed patterns like `count`)
  - Plugin model or policy engine abstraction (OPA-lite or Rego subset)
  - Inline policy validation with fast feedback (fail before plan)

---

## 3. Observability and Run UX

- **Current**: CLI-driven feedback loop
- **Recommended improvements**:
  - GitHub Checks dashboard per run
  - Run summary endpoint (`/runs/{id}/summary`) exposed via UI or API
  - DAG view: visualize status of each module in the plan/apply flow
  - Metrics for drift, plan duration, apply success, Sentinel fail/pass

---

## 4. Ecosystem Integration

- **Current**: GitHub PR checks + GitHub Actions interaction
- **Recommended improvements**:
  - GitHub App for PORC that surfaces blueprint status inline
  - Register PORC blueprints as services in Backstage or internal catalog
  - Optional Backstage plugin to show:
    - Blueprint inputs
    - Run history
    - Sentinel pass/fail
    - Blueprint links

---

## 5. Team Guardrails vs. Flexibility

- **Current**: Strict paved paths, no `.tf` overrides
- **Recommended improvements**:
  - Add flags for advanced teams to allow `.tf` overrides in sandboxed environments
  - Module version pinning with semantic ranges:
    - Example: `ref = "~> v1.0"` or allowlist enforced in PORC templates
  - Policy-based control over what overrides are allowed per environment tier

---

## Summary

PORC is strategically well-positioned. These enhancements would:
- Boost adoption through better UX and visibility
- Enable more nuanced policy enforcement
- Keep engineers inside GitHub while raising standards for delivery quality