# End-to-End Terraform Plan & Apply Flow with PORC + GitHub

This document explains how Terraform infrastructure is rendered, planned, and applied using a hybrid approach that includes PORC, GitHub Actions, and Terraform Enterprise.

## Overview

- **PORC** renders Terraform configurations from a blueprint
- **GitHub Actions** optionally execute `terraform plan` and `terraform apply`
- **Terraform Enterprise** stores the remote workspace, state, and executes runs
- **Approval flow** is controlled by PORC, optionally requiring change record validation (e.g., ServiceNow)

## Step-by-Step Flow

1. Blueprint submitted via GitHub or Port webhook
2. PORC validates blueprint and generates `.tf` and `.tfvars.json`
3. GitHub workflow runs `terraform plan` using `backend.hcl`
4. PORC logs plan result and tracks hash/approval
5. GitHub or PORC triggers `apply` if plan was successful
6. Sentinel policies run automatically in TFE
7. Results are logged, monitored, and auditable

## Decision Matrix

| Step         | Controlled By | Audit Location     | Alternate Option       |
|--------------|---------------|--------------------|------------------------|
| Render       | PORC          | Mongo              | None                   |
| Plan         | GitHub / PORC | GitHub Logs / Mongo| Native Terraform Cloud |
| Approval     | PORC          | ServiceNow / Mongo | GitHub PR review       |
| Apply        | GitHub / PORC | GitHub / Mongo     | Terraform UI button    |
| Policies     | Terraform     | TFE Sentinel logs  | None                   |