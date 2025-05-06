# PORC Documentation Index

This repository includes both API and CLI tools for orchestrating Terraform workflows from validated blueprints. Below is a list of key documentation files:
# Top-Level Docs

- [README.md](https://github.com/hyperfocus/porc/blob/main/README.md): Overview of PORC and PINE structure and usage
- [CHANGELOG.md](https://github.com/hyperfocus/porc/blob/main/CHANGELOG.md): Version history and changes
- [CONTRIBUTING.md](https://github.com/hyperfocus/porc/blob/main/CONTRIBUTING.md): How to contribute and PR guidelines
# Developer Guides

- [docs/architecture.md](https://github.com/hyperfocus/porc/blob/main/docs/architecture.md): High-level system design for API, CLI, and worker
- [pine/docs/usage.md](https://github.com/hyperfocus/porc/blob/main/pine/docs/usage.md): CLI command documentation
# GitHub Configs

- [.github/workflows/lint.yml](https://github.com/hyperfocus/porc/blob/main/.github/workflows/lint.yml): Lint blueprints on push
- [.github/workflows/test.yml](https://github.com/hyperfocus/porc/blob/main/.github/workflows/test.yml): Run Python unit tests
# Dev Containers

- [.devcontainer/devcontainer.json](https://github.com/hyperfocus/porc/blob/main/.devcontainer/devcontainer.json): Setup for GitHub Codespaces
# Examples and Schemas

- [examples/](https://github.com/hyperfocus/porc/tree/main/examples/): Example blueprints (GKE, Postgres)
- [rendered/](https://github.com/hyperfocus/porc/tree/main/rendered/): Generated Terraform files
- [schemas/](https://github.com/hyperfocus/porc/tree/main/schemas/): JSON schemas for blueprint validation

---

> For internal use across CI/CD, platform tooling, and developer self-service pipelines at scale.
# New API Routes
# GET `/run/{run_id}/status`
Returns lightweight status for polling or monitoring:
```json
{
  "run_id": "run-abc123",
  "status": "planned",
  "last_updated": "2025-05-05T12:00:00Z"
}
```
# GET `/run/{run_id}/summary`
Returns full metadata for external portals:
```json
{
  "run_id": "run-abc123",
  "status": "applied",
  "workspace_id": "ws-abc123",
  "blueprint": "gke-cluster/1.0.0",
  "repo_url": "...",
  "outputs": { "cluster_name": "...", "region": "..." }
}
```

This endpoint is intended for integration with systems like Port and Backstage.