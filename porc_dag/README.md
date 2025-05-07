# DAG Support for PORC and PINE

This directory provides support for dependency graph (DAG) handling for Terraform blueprints within the PORC platform and optional visual feedback via PINE.

---

## Contents

- `dag.py`: Core DAG logic (nodes, topological sort, cycle detection)
- `dag_tool.py`: High-level wrapper that processes a JSON blueprint and outputs:
  - Execution order
  - A DAG image (Graphviz `.png`)
- `porc_dag_api.py`: FastAPI route for PORC to expose a `/dag` endpoint

---

## PORC Integration

### Step 1: Include `dag_tool.py` in PORC backend
Import `process_blueprint()` and use it during blueprint submission or run initialization.

### Step 2: Register the API route
In your FastAPI app:
```python
from dag.porc_dag_api import router as dag_router
app.include_router(dag_router, prefix="/api")
```

### Step 3: Serve DAG Images
Ensure Graphviz outputs (`.png`) are saved to a `/static/` directory that is served via FastAPI:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
```

---

## PINE Integration

PINE can optionally visualize DAGs by calling the PORC `/api/dag` endpoint:

```bash
pine dag --blueprint path/to/blueprint.json
```

This can:
- Print the execution order
- Download and open the DAG image
- Or render inline if terminal supports it

Future: Add `pine graph` as a subcommand that renders the DAG locally from JSON.

---

## Sample Blueprint Format

```json
{
  "modules": [
    { "name": "network", "depends_on": [] },
    { "name": "db", "depends_on": ["network"] },
    { "name": "app", "depends_on": ["network"] },
    { "name": "frontend", "depends_on": ["app"] }
  ]
}
```

---

## Requirements

- `graphviz` must be installed on the server or dev machine.
- Python 3.8+