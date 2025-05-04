# PORC Documentation Index

This repository includes both API and CLI tools for orchestrating Terraform workflows from validated blueprints. Below is a list of key documentation files:

## Top-Level Docs

- [README.md](README.md): Overview of PORC and PINE structure and usage
- [CHANGELOG.md](CHANGELOG.md): Version history and changes
- [CONTRIBUTING.md](CONTRIBUTING.md): How to contribute and PR guidelines

## Developer Guides

- [docs/architecture.md](docs/architecture.md): High-level system design for API, CLI, and worker
- [pine/docs/usage.md](pine/docs/usage.md): CLI command documentation

## GitHub Configs

- [.github/workflows/lint.yml](.github/workflows/lint.yml): Lint blueprints on push
- [.github/workflows/test.yml](.github/workflows/test.yml): Run Python unit tests

## Dev Containers

- [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json): Setup for GitHub Codespaces

## Examples and Schemas

- [examples/](examples/): Example blueprints (GKE, Postgres)
- [rendered/](rendered/): Generated Terraform files
- [schemas/](schemas/): JSON schemas for blueprint validation

---

> For internal use across CI/CD, platform tooling, and developer self-service pipelines at scale.
