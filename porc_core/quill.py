"""
PORC Core QUILL: Qualified Infrastructure Layout Layer
Manages the rendering of infrastructure templates using Jinja2.
"""
import os
import logging
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
from .storage import get_storage_service

class QuillManager:
    def __init__(self):
        """Initialize the QUILL manager."""
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._storage_service = None
    
    @property
    def storage_service(self):
        """Lazy initialization of storage service."""
        if self._storage_service is None:
            self._storage_service = get_storage_service()
        return self._storage_service
    
    def get_quill(self, kind: str, version: str = "latest") -> Dict[str, str]:
        """Get the QUILL template for a given kind and version."""
        try:
            # Get template from storage
            templates = self.storage_service.get_quill(kind, version)
            
            # Create Jinja2 templates
            return {
                "main.tf": self.env.from_string(templates["main.tf"]),
                "terraform.tfvars.json": self.env.from_string(templates["terraform.tfvars.json"])
            }
        except Exception as e:
            logging.error(f"Failed to load QUILL template for kind {kind}: {str(e)}")
            raise ValueError(f"No QUILL template found for kind: {kind}")
    
    def render_quill(self, kind: str, variables: Dict[str, Any], version: str = "latest") -> Dict[str, str]:
        """Render a QUILL template with the given variables."""
        templates = self.get_quill(kind, version)
        
        try:
            return {
                "main.tf": templates["main.tf"].render(**variables),
                "terraform.tfvars.json": templates["terraform.tfvars.json"].render(**variables)
            }
        except Exception as e:
            logging.error(f"Failed to render QUILL template for kind {kind}: {str(e)}")
            raise ValueError(f"Failed to render QUILL template: {str(e)}")

# Initialize the QUILL manager
quill_manager = QuillManager() 