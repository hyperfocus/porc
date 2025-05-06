# GitHub Workflow Reference for PORC

This document describes each GitHub Action workflow included in the repository, along with required secrets and deployment roles.

---

## Workflows Summary

| Workflow File             | Trigger                         | Purpose                                      |
|---------------------------|----------------------------------|----------------------------------------------|
| `ci.yml`                  | Push/PR to `main`               | Lint and test with flake8/pytest             |
| `docker-push.yml`         | Push to `main` or tags (e.g. v1.0.0) | Build & push Docker image, deploy to AKS |
| `lint.yml`                | Any push                        | Run `flake8` on Python files                 |
| `pine-lint.yml`           | Any push or PR                  | Validate blueprint examples with `pine`      |
| `terraform-plan.yml`      | Manual / PR event               | Run `terraform plan`                         |
| `terraform-apply.yml`     | Manual / merge to main          | Run `terraform apply`                        |
| `test.yml`                | PR validation                   | Run `pytest` test suite                      |
| `wiki-sync.yml`           | Push to `main`, `docs/**`       | Sync markdown docs to GitHub Wiki            |

---

## Required GitHub Secrets

| Secret Name         | Used In                  | Description                                  |
|---------------------|--------------------------|----------------------------------------------|
| `GITHUB_TOKEN`      | `wiki-sync.yml`          | Auto-provided for pushing to GitHub Wiki     |
| `DOCKERHUB_USERNAME`| `docker-push.yml`        | DockerHub username                           |
| `DOCKERHUB_TOKEN`   | `docker-push.yml`        | DockerHub PAT or password                    |
| `TFE_TOKEN`         | `docker-push.yml`, App   | Token for Terraform Enterprise               |
| `AZURE_CREDENTIALS` | `docker-push.yml`        | JSON for `az login` to AKS                   |
| `AKS_RG`            | `docker-push.yml`        | Azure resource group name                    |
| `AKS_CLUSTER`       | `docker-push.yml`        | AKS cluster name                             |

---

## Notes

- Wiki sync works automatically if your repo's Wiki is enabled.
- Deployment uses Helm with `porc/helm/porc` and `--set` overrides.
- To run TFE commands from worker or API, ensure `TFE_TOKEN` is provided at runtime.