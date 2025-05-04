# PINE CLI Usage

## Validate a blueprint

```bash
pine validate examples/gke-blueprint.json
```

## Lint a blueprint

```bash
pine lint examples/postgres-blueprint.json
```

Optional:
- `--strict`: exits with error on warnings
- `--output lint.json`: writes lint warnings to file

