# How to Run Terraform Plan/Apply from GitHub

This guide explains how to run `terraform plan` and `terraform apply` in GitHub Actions after PORC has rendered and uploaded Terraform configuration.

## Requirements

- PORC must stage the config (main.tf, tfvars, backend.hcl)
- A valid remote workspace must exist in Terraform Enterprise
- A `TFE_TOKEN` must be stored as a GitHub Actions secret

## Terraform Backend Configuration

Your `development/backend.hcl` must look like:

```hcl
organization = "td-organization"

workspaces {
  name = "example-gke-cluster-dev"
}
```

## GitHub Workflow Steps

1. Use `hashicorp/setup-terraform` to install Terraform
2. Run `terraform init` with `-backend-config=development/backend.hcl`
3. Run `terraform plan` (or `apply`) with:

```yaml
terraform plan -var-file=terraform.tfvars.json -input=false
```

4. `TF_TOKEN_app_terraform_io` will authenticate CLI to TFE

## Apply Workflow

You can create a separate `terraform-apply.yml` using:

```yaml
terraform apply -var-file=terraform.tfvars.json -auto-approve
```

**Note:** Approvals can be enforced via Sentinel or PORC metadata.

## Auditing

GitHub run ID and repo name are used for tracing execution and workspace.