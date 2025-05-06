# Contributing to PORC

Thanks for helping improve PORC and PINE!
# Setup

```bash
git clone https://github.com/your-org/porc
cd porc
poetry install  # or pip install -r requirements.txt
```
# Development

- API: Run with `uvicorn porc_api.main:app --reload`
- CLI: Use `python pine/main.py validate examples/gke-blueprint.json`
# Pull Requests

- Use `scaffold/` or `feature/` prefixes for branches
- Include tests for new logic
- Update documentation if needed