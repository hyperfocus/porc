# PORC Deployment Guide

This document describes how to deploy and operate the PORC orchestrator service in both development and production environments.

---

## Local Development

### Prerequisites
- Python 3.9+
- `uvicorn`, `fastapi`, `httpx`, and other dependencies

### Run Locally
```bash
pip install -r requirements.txt
uvicorn porc_api.main:app --reload
```

This will start the service at: `http://127.0.0.1:8000`

Logs and audit files are written to:
- `/tmp/porc-audit/{run_id}.log`
- `/tmp/porc-metrics.jsonl`
- `/tmp/porc-metadata/{run_id}.json`

---

## Production Deployment

### Option 1: Gunicorn + Uvicorn Workers
```bash
pip install gunicorn uvicorn
gunicorn porc_api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

Use systemd or supervisord to keep the service running.

### Option 2: Docker (Recommended)
```Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "porc_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Build & run:
```bash
docker build -t porc .
docker run -d -p 8080:8080 porc
```

---

## Logging and Telemetry

- **Audit logs**: `/tmp/porc-audit/`
- **Metrics log**: `/tmp/porc-metrics.jsonl`
- **Terraform metadata**: `/tmp/porc-metadata/`
- **Placeholders**: Integration points exist for DataDog, Dynatrace

---

## External Access

Use a reverse proxy (e.g. nginx, envoy) in front of the FastAPI app for:
- HTTPS termination
- Auth headers
- Rate limiting

---

## Health Check (Optional)
Add a basic `/health` endpoint to `main.py`:
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

---

## Kubernetes Deployment with Helm

PORC is also deployable via a Helm chart.

### Prerequisites

- Kubernetes cluster access
- `helm` CLI installed
- A MongoDB service accessible from the cluster

### MongoDB Configuration

You must configure an external MongoDB instance and provide the connection string:

```yaml
mongo:
  uri: mongodb://your-mongo-host:27017/porc
```

This URI will be injected as the `MONGO_URI` environment variable.

### Install the Chart

```bash
helm install porc ./porc-helm   --set mongo.uri="mongodb://mongo.td.internal:27017/porc"
```

This will deploy:
- 1 replica of the PORC FastAPI app
- A `ClusterIP` service named `porc`
- `MONGO_URI` via ConfigMap

To expose via Ingress, uncomment and configure the `ingress.yaml` template.

## Environment Variables

The following environment variables are required for deployment:

- `TFE_TOKEN`: Terraform Cloud API token
- `TFE_API`: Terraform Cloud API URL (default: https://app.terraform.io/api/v2)
- `TFE_ORG`: Terraform Cloud organization name
- `TFE_ENV`: Environment name (e.g., dev, prod)
- `MONGO_URI`: MongoDB connection string
- `GITHUB_REPOSITORY`: GitHub repository name

## Kubernetes Secrets

Create the following secrets:

```bash
# Terraform Cloud token
kubectl create secret generic tfe-secrets \
  --from-literal=TFE_TOKEN=your-token-here

# MongoDB connection string
kubectl create secret generic mongo-secrets \
  --from-literal=MONGO_URI=your-mongo-uri-here
```

## Helm Installation

1. Add the Helm repository:
```bash
helm repo add porc https://porcupine.azurecr.io/helm
```

2. Install the chart:
```bash
helm install porc porc/porc \
  --set tfe.org=your-org \
  --set tfe.env=dev \
  --set github.repository=your-org/porc
```

## Configuration

The following values can be configured in `values.yaml`:

```yaml
tfe:
  api: "https://app.terraform.io/api/v2"
  org: "your-org"
  env: "dev"
  tokenSecretName: tfe-secrets

github:
  repository: "your-org/porc"
```

## Ingress Configuration

The default ingress configuration uses NGINX:

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/healthcheck-path: /health
    nginx.ingress.kubernetes.io/healthcheck-interval: "10s"
    nginx.ingress.kubernetes.io/healthcheck-timeout: "5s"
    nginx.ingress.kubernetes.io/healthcheck-fails: "3"
    nginx.ingress.kubernetes.io/healthcheck-passes: "3"
```

## Resource Requirements

Default resource limits and requests:

```yaml
resources:
  limits:
    cpu: 250m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi
```

