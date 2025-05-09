"""
Test script for TFE client functionality.
"""
import logging
import os
from porc_core.tfe_client import TFEClient

# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

def test_workspace_access():
    """Test accessing a workspace and its configuration versions."""
    client = TFEClient()
    
    try:
        # Try to get workspace ID
        workspace_name = "porc-dev"
        print(f"\nTesting workspace access for: {workspace_name}")
        workspace_id = client.get_workspace_id(workspace_name)
        print(f"Successfully got workspace ID: {workspace_id}")
        
        # Try to list configuration versions
        print(f"\nTesting configuration versions for workspace: {workspace_id}")
        url = f"workspaces/{workspace_id}/configuration-versions"
        response = client._request_with_retries("GET", url)
        print("Successfully retrieved configuration versions")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    test_workspace_access() 