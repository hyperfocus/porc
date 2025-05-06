![PORC Logo](logo.png)

# Getting Started with PORC
# Quickstart (CLI)

```bash
# Validate a blueprint
python pine/main.py lint examples/gke-blueprint.json
```
# Quickstart (API)

```bash
curl -X POST http://localhost:8000/blueprint \
  -H "Content-Type: application/json" \
  -d @examples/gke-blueprint.json
```
# Deploy on AKS (Helm)

```bash
helm upgrade --install porc ./helm/porc \
  --set image.repository=yourrepo/porc \
  --set env.TFE_TOKEN=$TFE_TOKEN \
  --set mongo.uri="mongodb://..."
```