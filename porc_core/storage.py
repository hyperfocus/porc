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
import boto3
from botocore.exceptions import ClientError

class StorageService:
    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize storage service with S3 bucket."""
        self.bucket_name = bucket_name or os.getenv("PORC_STORAGE_BUCKET")
        if not self.bucket_name:
            raise ValueError("Storage bucket name is required")
        
        self.s3 = boto3.client('s3')
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists."""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                self.s3.create_bucket(Bucket=self.bucket_name)
                logging.info(f"Created storage bucket: {self.bucket_name}")
    
    def store_deployment_bundle(self, run_id: str, files: Dict[str, str]) -> str:
        """Store deployment bundle in S3 and return the bundle key."""
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                for name, content in files.items():
                    zf.writestr(name, content)
        
        # Upload to S3
        bundle_key = f"bundles/{run_id}/{datetime.utcnow().isoformat()}.zip"
        try:
            self.s3.upload_file(tmp.name, self.bucket_name, bundle_key)
            logging.info(f"Stored deployment bundle: {bundle_key}")
            return bundle_key
        finally:
            os.unlink(tmp.name)  # Clean up temp file
    
    def get_deployment_bundle(self, bundle_key: str) -> BinaryIO:
        """Get deployment bundle from S3."""
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=bundle_key)
            return response['Body']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ValueError(f"Deployment bundle not found: {bundle_key}")
            raise
    
    def store_quill(self, kind: str, version: str, templates: Dict[str, str]) -> str:
        """Store QUILL template in S3 and return the template key."""
        template_key = f"quills/{kind}/{version}/templates.json"
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=template_key,
                Body=json.dumps(templates),
                ContentType='application/json'
            )
            logging.info(f"Stored QUILL template: {template_key}")
            return template_key
        except ClientError as e:
            raise ValueError(f"Failed to store QUILL template: {str(e)}")
    
    def get_quill(self, kind: str, version: str) -> Dict[str, str]:
        """Get QUILL template from S3."""
        template_key = f"quills/{kind}/{version}/templates.json"
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=template_key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ValueError(f"QUILL template not found: {template_key}")
            raise

# Initialize the storage service
storage_service = StorageService() 