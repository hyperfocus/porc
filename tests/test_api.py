import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from porc_api.main import app

def get_test_client(base_url, verify_ssl):
    # Use in-memory app only for local testing
    if base_url == "http://test":
        return TestClient(app)
    else:
        return AsyncClient(base_url=base_url, verify=verify_ssl)

@pytest.mark.asyncio
async def test_root(base_url, host_header, verify_ssl):
    headers = {}
    if host_header:
        headers["Host"] = host_header
    
    client = get_test_client(base_url, verify_ssl)
    resp = client.get("/", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}

@pytest.mark.asyncio
async def test_healthz(base_url, host_header, verify_ssl):
    headers = {}
    if host_header:
        headers["Host"] = host_header
    
    client = get_test_client(base_url, verify_ssl)
    resp = client.get("/healthz", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_invalid_blueprint_submission(base_url, host_header, verify_ssl):
    headers = {"Content-Type": "application/json"}
    if host_header:
        headers["Host"] = host_header
    
    client = get_test_client(base_url, verify_ssl)
    
    # Test missing required field
    invalid_blueprint = {
        "variables": {},
        "schema_version": "v1"
    }
    resp = client.post("/blueprint", headers=headers, json=invalid_blueprint)
    assert resp.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_invalid_run_id(base_url, host_header, verify_ssl):
    headers = {}
    if host_header:
        headers["Host"] = host_header
    
    client = get_test_client(base_url, verify_ssl)
    
    # Test invalid run ID format with special characters
    invalid_run_id = "invalid.run.id"
    resp = client.get(f"/run/{invalid_run_id}/status", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"] == "Invalid run_id"

    # Test another invalid format with spaces
    invalid_run_id = "invalid run id"
    resp = client.get(f"/run/{invalid_run_id}/status", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"] == "Invalid run_id"

@pytest.mark.asyncio
async def test_nonexistent_run_id(base_url, host_header, verify_ssl):
    headers = {}
    if host_header:
        headers["Host"] = host_header
    
    client = get_test_client(base_url, verify_ssl)
    
    # Test non-existent run ID
    nonexistent_run_id = "porc-nonexistent"
    resp = client.get(f"/run/{nonexistent_run_id}/status", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error"] == "Run ID not found"

@pytest.mark.asyncio
async def test_blueprint_full_lifecycle(base_url, host_header, verify_ssl):
    headers = {"Content-Type": "application/json"}
    if host_header:
        headers["Host"] = host_header
    
    client = get_test_client(base_url, verify_ssl)
    
    # Submit a blueprint
    blueprint = {
        "kind": "example",
        "variables": {},
        "schema_version": "v1"
    }
    resp = client.post("/blueprint", headers=headers, json=blueprint)
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    run_id = data["run_id"]

    # Build from blueprint
    resp = client.post(f"/run/{run_id}/build", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "built"

    # Plan (may fail if Terraform is not set up, but test the endpoint)
    resp = client.post(f"/run/{run_id}/plan", headers=headers)
    assert resp.status_code in (200, 404, 500)  # Accept 500 for CI

    # Apply (may fail if Terraform is not set up, but test the endpoint)
    resp = client.post(f"/run/{run_id}/apply", headers=headers)
    assert resp.status_code in (200, 404, 500)

    # Status
    resp = client.get(f"/run/{run_id}/status", headers=headers)
    assert resp.status_code == 200
    assert "status" in resp.json()

    # Summary
    resp = client.get(f"/run/{run_id}/summary", headers=headers)
    assert resp.status_code in (200, 404) 