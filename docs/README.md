![PORC Logo](logo.png)

# PORC Documentation Index

Welcome to the documentation for **PORC** (Platform Orchestrator) and **PINE** (PORC Infrastructure Negotiation Engine).  
This system enables Terraform-based paved paths with policy enforcement, approval control, and Port integration.

---

## Documentation Contents

### System Overview
- [Architecture](https://github.com/hyperfocus/porc/blob/main/docs/Architecture.md) – Component breakdown, flowcharts, and storage model
- [flowchart.mmd](flowchart.mmd) – Standalone Mermaid diagram source

### Core Interfaces
- [API Reference](https://github.com/hyperfocus/porc/blob/main/docs/API.md) – REST API for blueprint processing, run orchestration, logging, and reporting
- [PINE CLI Reference](https://github.com/hyperfocus/porc/blob/main/docs/PINE-CLI.md) – Command-line tool for blueprint validation and rendering

### Policy, Compliance & Governance
- [Blueprint Security Checks](https://github.com/hyperfocus/porc/blob/main/docs/Blueprint-Security.md) – Early validation rules applied by PINE
- [Sentinel Policy Enforcement](https://github.com/hyperfocus/porc/blob/main/docs/Sentinel-Policies.md) – Remote Sentinel execution in TFE
- [Approval & Change Control](https://github.com/hyperfocus/porc/blob/main/docs/Approvals.md) – ServiceNow integration and override rules

### Integrations
- [Port Sync Guide](https://github.com/hyperfocus/porc/blob/main/docs/Port-Sync.md) – How PORC syncs metadata to Port using Terraform provider

### Metadata & Reports
- [Metadata Spec](https://github.com/hyperfocus/porc/blob/main/docs/Metadata.md) – Format and fields used for PORC run tracking
- [Report API](API.md#reporting) – View logs, run files, and status summaries

---

## Usage

Documentation is stored in the `/docs` directory of this repo and can also be synced to the GitHub Wiki (if enabled).

To regenerate the wiki:
```bash
gh workflow run sync-wiki.yml
```

---

## Versioning

Current version: `v1.0`  
Last updated: May 2025
---

## Usage (Docker)

### Pull from GitHub Container Registry (GHCR)
```bash
docker pull ghcr.io/hyperfocus/porc:latest
```

### Run PORC locally
```bash
docker run -d \
  -p 8000:8000 \
  --name porc \
  -e ENV=dev \
  ghcr.io/hyperfocus/porc:latest
```

### Test the API
```bash
curl http://localhost:8000/healthz
```