"""
PORC Core Render: Blueprint rendering for PORC system.
"""
import logging
import sys
import json
import os

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'name': record.name,
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)

def render_gke_cluster(blueprint):
    """Render Terraform for GKE cluster blueprint."""
    inputs = blueprint.get("inputs", {})
    cluster_name = inputs.get("cluster_name", "default-cluster")
    region = inputs.get("region", "us-central1")
    node_count = inputs.get("node_count", 3)
    
    return {
        "main.tf": f"""module "gke_cluster" {{
  source       = "git::https://git.td.com/terraform-modules/gke.git"
  cluster_name = "{cluster_name}"
  region       = "{region}"
  node_count   = {node_count}
}}""",
        "terraform.tfvars.json": json.dumps({
            "cluster_name": cluster_name,
            "region": region,
            "node_count": node_count
        }, indent=2)
    }

def render_postgres_db(blueprint):
    """Render Terraform for Postgres database blueprint."""
    inputs = blueprint.get("inputs", {})
    db_name = inputs.get("db_name", "default-db")
    db_user = inputs.get("db_user", "tdadmin")
    plan = inputs.get("plan", "standard")
    
    return {
        "main.tf": f"""module "postgres_db" {{
  source  = "git::https://git.td.com/terraform-modules/postgres.git"
  db_name = "{db_name}"
  db_user = "{db_user}"
  plan    = "{plan}"
}}""",
        "terraform.tfvars.json": json.dumps({
            "db_name": db_name,
            "db_user": db_user,
            "plan": plan
        }, indent=2)
    }

def render_blueprint(blueprint):
    """Render a blueprint into Terraform files."""
    kind = blueprint.get("kind")
    if not kind:
        raise ValueError("Blueprint must specify a 'kind'")
    
    # Map blueprint kinds to render functions
    renderers = {
        "gke-cluster": render_gke_cluster,
        "postgres-db": render_postgres_db
    }
    
    renderer = renderers.get(kind)
    if not renderer:
        raise ValueError(f"Unsupported blueprint kind: {kind}")
    
    logging.info(f"Rendering blueprint of kind: {kind}")
    return renderer(blueprint) 