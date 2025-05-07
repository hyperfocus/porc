"""
PORC Core Storage: Manages storage of deployment bundles and QUILLs.
"""
import os
import logging
import json
import tempfile
import zipfile
from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError

class StorageService:
    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize storage service with Azure Blob Storage."""
        self.bucket_name = bucket_name or os.getenv("STORAGE_BUCKET")
        if not self.bucket_name:
            raise ValueError("Storage bucket name is required")
        
        account_name = os.getenv("STORAGE_ACCOUNT")
        account_key = os.getenv("STORAGE_ACCESS_KEY")
        
        if not account_name or not account_key:
            raise ValueError("Azure Storage account name and access key are required")
        
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Ensure the storage container exists."""
        try:
            self.blob_service.get_container_client(self.bucket_name).get_container_properties()
        except ResourceNotFoundError:
            self.blob_service.create_container(self.bucket_name)
            logging.info(f"Created storage container: {self.bucket_name}")
    
    def store_deployment_bundle(self, run_id: str, files: Dict[str, str]) -> str:
        """Store deployment bundle in Azure Blob Storage and return the bundle key."""
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                for name, content in files.items():
                    zf.writestr(name, content)
        
        # Upload to Azure Blob Storage
        bundle_key = f"bundles/{run_id}/{datetime.utcnow().isoformat()}.zip"
        try:
            blob_client = self.blob_service.get_blob_client(container=self.bucket_name, blob=bundle_key)
            with open(tmp.name, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)
            logging.info(f"Stored deployment bundle: {bundle_key}")
            return bundle_key
        finally:
            os.unlink(tmp.name)  # Clean up temp file
    
    def get_deployment_bundle(self, bundle_key: str) -> BinaryIO:
        """Get deployment bundle from Azure Blob Storage."""
        try:
            blob_client = self.blob_service.get_blob_client(container=self.bucket_name, blob=bundle_key)
            return blob_client.download_blob().readall()
        except ResourceNotFoundError:
            raise ValueError(f"Deployment bundle not found: {bundle_key}")
    
    def store_quill(self, kind: str, version: str, templates: Dict[str, str]) -> str:
        """Store QUILL template in Azure Blob Storage and return the template key."""
        template_key = f"quills/{kind}/{version}/templates.json"
        try:
            blob_client = self.blob_service.get_blob_client(container=self.bucket_name, blob=template_key)
            blob_client.upload_blob(
                json.dumps(templates),
                overwrite=True,
                content_settings={'content_type': 'application/json'}
            )
            logging.info(f"Stored QUILL template: {template_key}")
            return template_key
        except Exception as e:
            raise ValueError(f"Failed to store QUILL template: {str(e)}")
    
    def get_quill(self, kind: str, version: str) -> Dict[str, str]:
        """Get QUILL template from Azure Blob Storage."""
        template_key = f"quills/{kind}/{version}/templates.json"
        try:
            blob_client = self.blob_service.get_blob_client(container=self.bucket_name, blob=template_key)
            return json.loads(blob_client.download_blob().readall().decode('utf-8'))
        except ResourceNotFoundError:
            raise ValueError(f"QUILL template not found: {template_key}")

# Initialize the storage service
storage_service = StorageService() 