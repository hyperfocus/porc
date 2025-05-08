"""
Template Validation: Validates QUILL template structure and content.
"""
import os
import json
import logging
from pathlib import Path
from jinja2 import Environment, TemplateSyntaxError

# Configure logging
logging.basicConfig(level=logging.INFO)

def validate_template_syntax(template_content):
    """Validate Jinja2 template syntax."""
    try:
        Environment().parse(template_content)
        return True
    except TemplateSyntaxError as e:
        logging.error(f"Template syntax error: {e}")
        return False

def validate_template_structure():
    """Validate template directory structure and content."""
    quills_dir = Path("quills")
    if not quills_dir.exists():
        raise ValueError("quills directory not found")
    
    errors = []
    
    # Process each template kind
    for kind_dir in quills_dir.iterdir():
        if not kind_dir.is_dir():
            continue
            
        kind = kind_dir.name
        logging.info(f"Validating kind: {kind}")
        
        # Check for version directories
        version_dirs = [d for d in kind_dir.iterdir() if d.is_dir() and d.name != "latest"]
        if not version_dirs:
            errors.append(f"No version directories found for kind: {kind}")
            continue
        
        # Process each version
        for version_dir in version_dirs:
            version = version_dir.name
            logging.info(f"Validating version: {version}")
            
            # Check for template files
            template_files = list(version_dir.glob("*.j2"))
            if not template_files:
                errors.append(f"No template files found in {version_dir}")
                continue
            
            # Validate each template
            for template_file in template_files:
                with open(template_file, "r") as f:
                    content = f.read()
                    if not validate_template_syntax(content):
                        errors.append(f"Invalid template syntax in {template_file}")
            
            # Check for required templates
            required_templates = ["main.tf.j2", "terraform.tfvars.json.j2"]
            missing_templates = [t for t in required_templates if not (version_dir / t).exists()]
            if missing_templates:
                errors.append(f"Missing required templates in {version_dir}: {missing_templates}")
    
    if errors:
        logging.error("Template validation failed:")
        for error in errors:
            logging.error(f"- {error}")
        return False
    
    logging.info("Template validation passed")
    return True

if __name__ == "__main__":
    if not validate_template_structure():
        exit(1) 