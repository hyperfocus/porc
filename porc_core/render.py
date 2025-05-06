import json


def render_blueprint(blueprint: dict) -> dict:
    kind = blueprint["kind"]
    tfvars = blueprint.get("variables", {})

    main_tf = f'module "{kind}" {{\n  source = "registry.td.com/{kind}"\n}}'
    tfvars_json = json.dumps(tfvars, indent=2)

    return {
        "main.tf": main_tf,
        "terraform.tfvars.json": tfvars_json
    }
