# PINE CLI Reference

This page documents how to use the PINE CLI.

> Looking for when and why to use PINE in your platform workflow?  
> See [PINE Usage Guide](./PINE%20Usage%20Guide.md)

---

## Setup

```bash
export PORC_TOKEN=<your-api-token>
```

## Commands

### Local-only
- `pine lint <file>`
- `pine validate <file>`

### PORC-integrated
- `pine submit <blueprint.json>`
- `pine build --run-id <id>`
- `pine plan --run-id <id>`
- `pine apply --run-id <id>`

See [PINE CLI Reference](./PINE%20CLI%20Reference.md) for full examples and flags.