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
import asyncio

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
        self._table_service = None
        self._table_client = None
    
    @property
    def table_service(self) -> TableServiceClient:
        """Get the table service client, initializing it if needed."""
        if self._table_service is None:
            account_name = os.getenv("STORAGE_ACCOUNT")
            account_key = os.getenv("STORAGE_ACCESS_KEY")
            if not account_name or not account_key:
                raise ValueError("Azure Storage account name and access key are required")
            
            connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
            self._table_service = TableServiceClient.from_connection_string(connection_string)
            self._ensure_table_exists()
        return self._table_service
    
    @property
    def table_client(self) -> TableClient:
        """Get the table client, initializing it if needed."""
        if self._table_client is None:
            self._table_client = self.table_service.get_table_client(self.table_name)
        return self._table_client
    
    def _ensure_table_exists(self):
        """Ensure the state table exists."""
        try:
            self._table_service.create_table(self.table_name)
            logging.info(f"Created state table: {self.table_name}")
        except ResourceExistsError:
            logging.info(f"Using existing state table: {self.table_name}")
    
    async def get_state(self, run_id: str) -> Dict[str, Any]:
        """Get the current state of a run."""
        try:
            # Run the synchronous Azure Table Storage operation in a thread pool
            loop = asyncio.get_event_loop()
            entity = await loop.run_in_executor(
                None,
                lambda: self.table_client.get_entity(partition_key=run_id, row_key=run_id)
            )
            
            # Convert entity to dictionary and parse metadata if present
            state_dict = {
                "state": entity.get("state", RunState.SUBMITTED.value),
                "workspace": entity.get("workspace"),
                "updated_at": entity.get("updated_at"),
                "metadata": {}
            }
            
            # Parse metadata if present
            if "metadata" in entity:
                try:
                    if isinstance(entity["metadata"], str):
                        state_dict["metadata"] = json.loads(entity["metadata"])
                    elif isinstance(entity["metadata"], dict):
                        state_dict["metadata"] = entity["metadata"]
                except json.JSONDecodeError:
                    logging.warning(f"Failed to parse metadata JSON for run {run_id}")
            
            return state_dict
            
        except ResourceNotFoundError:
            # Return default state for new runs
            return {
                "state": RunState.SUBMITTED.value,
                "metadata": {}
            }
        except Exception as e:
            logging.error(f"Failed to get state for run {run_id}: {str(e)}")
            # Return default state on error
            return {
                "state": RunState.SUBMITTED.value,
                "metadata": {}
            }
    
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

def get_state_service() -> StateService:
    """Get a state service instance."""
    return StateService()

# Initialize the state service
state_service = get_state_service() 