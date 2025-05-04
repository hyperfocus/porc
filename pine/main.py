import typer
import json
import re
from pathlib import Path
from jsonschema import validate as json_validate, ValidationError

app = typer.Typer()

SCHEMA_DIR = Path("schemas")
POLICY_FILE = SCHEMA_DIR / "blueprint_metadata_policy.json"

@app.command()
def validate(file: Path):
    """Validate a blueprint against metadata and input schema."""
    blueprint = json.loads(file.read_text())

    with open(POLICY_FILE) as f:
        policy = json.load(f)

    errors = []
    for field, rule in policy.items():
        if rule == "required" and field not in blueprint:
            errors.append(f"Missing required field: {field}")
        elif rule.startswith("required_if"):
            cond_field, cond_value = rule.split(":")[1].split("=")
            if blueprint.get(cond_field) == json.loads(cond_value) and field not in blueprint:
                errors.append(f"{field} is required when {cond_field}={cond_value}")

    if not errors:
        schema_path = SCHEMA_DIR / blueprint["kind"] / f"{blueprint['schema_version']}.json"
        if not schema_path.exists():
            typer.echo(f"Schema not found: {schema_path}")
            raise typer.Exit(code=2)
        schema = json.loads(schema_path.read_text())
        try:
            json_validate(instance=blueprint["inputs"], schema=schema)
        except ValidationError as e:
            errors.append(str(e))

    if errors:
        typer.echo("INVALID")
        for err in errors:
            typer.echo(f" - {err}")
        raise typer.Exit(code=1)

    typer.echo("VALID")

@app.command()
def lint(file: Path, strict: bool = False, output: Path = None):
    """Lint blueprint for best practice issues."""
    blueprint = json.loads(file.read_text())
    warnings = []

    if "description" not in blueprint:
        warnings.append("L001: Missing recommended field: description")

    owner = blueprint.get("owner", "")
    if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", owner):
        warnings.append(f"L002: Owner is not a valid email: '{owner}'")

    known_kinds = [p.name for p in SCHEMA_DIR.iterdir() if p.is_dir()]
    if blueprint.get("kind") not in known_kinds:
        warnings.append(f"L003: Kind '{blueprint.get('kind')}' is not recognized")

    if output:
        output.write_text(json.dumps({"warnings": warnings}, indent=2))

    if warnings:
        for w in warnings:
            typer.echo(f"WARNING {w}")
        if strict:
            raise typer.Exit(code=1)
    else:
        typer.echo("No warnings found.")

if __name__ == "__main__":
    app()