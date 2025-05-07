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
import boto3
from botocore.exceptions import ClientError

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
        """Initialize state service with DynamoDB table."""
        self.table_name = table_name or os.getenv("PORC_STATE_TABLE")
        if not self.table_name:
            raise ValueError("State table name is required")
        
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the state table exists."""
        try:
            self.table.table_status
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self.table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {'AttributeName': 'run_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'run_id', 'AttributeType': 'S'},
                        {'AttributeName': 'workspace', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'workspace-index',
                            'KeySchema': [
                                {'AttributeName': 'workspace', 'KeyType': 'HASH'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                self.table.wait_until_exists()
                logging.info(f"Created state table: {self.table_name}")
    
    def get_state(self, run_id: str) -> Dict[str, Any]:
        """Get the current state of a run."""
        try:
            response = self.table.get_item(Key={'run_id': run_id})
            return response.get('Item', {})
        except ClientError as e:
            raise ValueError(f"Failed to get state: {str(e)}")
    
    def update_state(self, run_id: str, state: RunState, 
                    workspace: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update the state of a run."""
        try:
            # Check for concurrent operations on the same workspace
            if workspace:
                response = self.table.query(
                    IndexName='workspace-index',
                    KeyConditionExpression='workspace = :ws',
                    FilterExpression='state IN (:planning, :applying)',
                    ExpressionAttributeValues={
                        ':ws': workspace,
                        ':planning': RunState.PLANNING.value,
                        ':applying': RunState.APPLYING.value
                    }
                )
                if response.get('Items'):
                    raise ValueError(f"Workspace {workspace} has a concurrent operation in progress")
            
            # Update the state
            item = {
                'run_id': run_id,
                'state': state.value,
                'updated_at': datetime.utcnow().isoformat()
            }
            if workspace:
                item['workspace'] = workspace
            if metadata:
                item['metadata'] = metadata
            
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise ValueError(f"Failed to update state: {str(e)}")
    
    def acquire_lock(self, workspace: str, run_id: str, ttl: int = 300) -> bool:
        """Acquire a lock for a workspace operation."""
        try:
            self.table.put_item(
                Item={
                    'run_id': f"lock:{workspace}",
                    'workspace': workspace,
                    'locked_by': run_id,
                    'expires_at': int(time.time()) + ttl
                },
                ConditionExpression='attribute_not_exists(run_id) OR expires_at < :now',
                ExpressionAttributeValues={
                    ':now': int(time.time())
                }
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise
    
    def release_lock(self, workspace: str, run_id: str):
        """Release a workspace lock."""
        try:
            self.table.delete_item(
                Key={'run_id': f"lock:{workspace}"},
                ConditionExpression='locked_by = :run_id',
                ExpressionAttributeValues={
                    ':run_id': run_id
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                raise

# Initialize the state service
state_service = StateService() 