# GitHub Secrets Configuration for PORC Workflows

To enable full CI/CD and deployment to AKS, the following secrets must be configured in your repository.

Go to: **GitHub > Settings > Secrets and Variables > Actions**

---
# Required Secrets

| Secret Name         | Description                                                          |
|---------------------|----------------------------------------------------------------------|

| `TFE_TOKEN`         | Terraform Enterprise API token for plan/apply operations             |
| `AZURE_CREDENTIALS` | Output of `az ad sp create-for-rbac --sdk-auth`                      |
| `AKS_RG`            | Azure Resource Group containing your AKS cluster                     |
| `AKS_CLUSTER`       | Name of the AKS cluster                                               |
| `WIKI_TOKEN` (optional) | GitHub PAT for pushing to the Wiki (if `GITHUB_TOKEN` isn't enough) |

---
# Example: Creating AZURE_CREDENTIALS

```bash
az ad sp create-for-rbac --name porc-ci   --role contributor   --scopes /subscriptions/<sub>/resourceGroups/<rg>   --sdk-auth
```

Copy the entire JSON output into the `AZURE_CREDENTIALS` secret.

---
# Notes

- `docker-push.yml` requires all secrets to build and deploy
- `wiki-sync.yml` works with `GITHUB_TOKEN`, but can use `WIKI_TOKEN` for finer control
- Ensure your Wiki is enabled before syncing