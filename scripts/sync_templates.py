"""
Template Sync: Syncs QUILL templates from local filesystem to Azure Storage.
"""
import os
import json
import logging
from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_storage_client():
    """Get Azure Storage client."""
    account_name = os.getenv("STORAGE_ACCOUNT")
    account_key = os.getenv("STORAGE_ACCESS_KEY")
    bucket_name = os.getenv("STORAGE_BUCKET")
    
    if not all([account_name, account_key, bucket_name]):
        raise ValueError("Missing required environment variables")
    
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    return BlobServiceClient.from_connection_string(connection_string), bucket_name

def ensure_container_exists(client, container_name):
    """Ensure storage container exists."""
    try:
        client.get_container_client(container_name).get_container_properties()
    except ResourceNotFoundError:
        client.create_container(container_name)
        logging.info(f"Created container: {container_name}")

def sync_templates():
    """Sync templates from local filesystem to Azure Storage."""
    client, bucket_name = get_storage_client()
    ensure_container_exists(client, bucket_name)
    
    quills_dir = Path("quills")
    if not quills_dir.exists():
        raise ValueError("quills directory not found")
    
    # Process each template kind
    for kind_dir in quills_dir.iterdir():
        if not kind_dir.is_dir():
            continue
            
        kind = kind_dir.name
        logging.info(f"Processing kind: {kind}")
        
        # Process each version
        for version_dir in kind_dir.iterdir():
            if not version_dir.is_dir() or version_dir.name == "latest":
                continue
                
            version = version_dir.name
            logging.info(f"Processing version: {version}")
            
            # Collect all template files
            templates = {}
            for template_file in version_dir.glob("*.j2"):
                with open(template_file, "r") as f:
                    templates[template_file.name] = f.read()
            
            if not templates:
                logging.warning(f"No templates found in {version_dir}")
                continue
            
            # Store templates in Azure
            template_key = f"quills/{kind}/{version}/templates.json"
            blob_client = client.get_blob_client(container=bucket_name, blob=template_key)
            content_settings = ContentSettings(content_type='application/json')
            blob_client.upload_blob(
                json.dumps(templates),
                overwrite=True,
                content_settings=content_settings
            )
            logging.info(f"Stored templates: {template_key}")
            
            # Update latest symlink
            latest_key = f"quills/{kind}/latest/templates.json"
            blob_client = client.get_blob_client(container=bucket_name, blob=latest_key)
            blob_client.upload_blob(
                json.dumps(templates),
                overwrite=True,
                content_settings=content_settings
            )
            logging.info(f"Updated latest: {latest_key}")

if __name__ == "__main__":
    sync_templates() 