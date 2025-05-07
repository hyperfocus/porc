"""
PORC Core State: Manages run states and concurrency control.
"""
import os
import logging
import json
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

class RunState(str, Enum):
    SUBMITTED = "submitted"
    BUILDING = "building"
    BUILT = "built"
    PLANNING = "planning"
    PLANNED = "planned"
    PLAN_FAILED = "plan_failed"
    APPLYING = "applying"
    APPLIED = "applied"
    APPLY_FAILED = "apply_failed"
    CANCELLED = "cancelled"

class StateService:
    def __init__(self, table_name: Optional[str] = None):
        """Initialize state service with Azure Table Storage."""
        self.table_name = table_name or os.getenv("PORC_STATE_TABLE", "porcstate")
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("Azure Storage connection string is required")
        
        self.table_service = TableServiceClient.from_connection_string(self.connection_string)
        self.table_client = self._get_table_client()
        self._ensure_table_exists()
    
    def _get_table_client(self) -> TableClient:
        """Get or create table client."""
        return self.table_service.get_table_client(self.table_name)
    
    def _ensure_table_exists(self):
        """Ensure the state table exists."""
        try:
            self.table_service.create_table(self.table_name)
            logging.info(f"Created state table: {self.table_name}")
        except ResourceExistsError:
            logging.info(f"Using existing state table: {self.table_name}")
    
    def get_state(self, run_id: str) -> Dict[str, Any]:
        """Get the current state of a run."""
        try:
            entity = self.table_client.get_entity(partition_key=run_id, row_key=run_id)
            return dict(entity)
        except ResourceNotFoundError:
            return {}
        except Exception as e:
            raise ValueError(f"Failed to get state: {str(e)}")
    
    def update_state(self, run_id: str, state: RunState, 
                    workspace: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update the state of a run."""
        try:
            # Check for concurrent operations on the same workspace
            if workspace:
                query = f"workspace eq '{workspace}' and (state eq '{RunState.PLANNING.value}' or state eq '{RunState.APPLYING.value}')"
                entities = self.table_client.query_entities(query)
                if list(entities):
                    raise ValueError(f"Workspace {workspace} has a concurrent operation in progress")
            
            # Update the state
            entity = {
                'PartitionKey': run_id,
                'RowKey': run_id,
                'state': state.value,
                'updated_at': datetime.utcnow().isoformat()
            }
            if workspace:
                entity['workspace'] = workspace
            if metadata:
                entity['metadata'] = json.dumps(metadata)
            
            self.table_client.upsert_entity(entity)
            return entity
        except Exception as e:
            raise ValueError(f"Failed to update state: {str(e)}")
    
    def acquire_lock(self, workspace: str, run_id: str, ttl: int = 300) -> bool:
        """Acquire a lock for a workspace operation."""
        try:
            entity = {
                'PartitionKey': f"lock:{workspace}",
                'RowKey': f"lock:{workspace}",
                'workspace': workspace,
                'locked_by': run_id,
                'expires_at': int(time.time()) + ttl
            }
            self.table_client.upsert_entity(entity)
            return True
        except Exception as e:
            logging.error(f"Failed to acquire lock: {str(e)}")
            return False
    
    def release_lock(self, workspace: str, run_id: str):
        """Release a workspace lock."""
        try:
            self.table_client.delete_entity(
                partition_key=f"lock:{workspace}",
                row_key=f"lock:{workspace}"
            )
        except Exception as e:
            logging.error(f"Failed to release lock: {str(e)}")

# Initialize the state service
state_service = StateService() 