from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .dag_tool import process_blueprint

router = APIRouter()

class Module(BaseModel):
    name: str
    depends_on: List[str] = []

class BlueprintRequest(BaseModel):
    modules: List[Module]
    output_prefix: str = "blueprint_dag"

@router.post("/dag")
def generate_dag(blueprint: BlueprintRequest):
    """
    Generate a DAG from module dependencies.
    Returns topological execution order and DAG image URL.
    """
    try:
        blueprint_dict = {
            "modules": [module.dict() for module in blueprint.modules]
        }
        execution_order, image_path = process_blueprint(blueprint_dict, blueprint.output_prefix)
        return {
            "execution_order": execution_order,
            "dag_image_url": f"/static/{image_path}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))