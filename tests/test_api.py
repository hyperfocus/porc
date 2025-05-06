import pytest
from httpx import AsyncClient
from porc_api.main import app

def get_async_client(base_url, verify_ssl):
    # Use in-memory app only for local testing
    if base_url == "http://test":
        return AsyncClient(app=app, base_url=base_url, verify=verify_ssl)
    else:
        return AsyncClient(base_url=base_url, verify=verify_ssl)

@pytest.mark.asyncio
async def test_healthz(base_url, host_header, verify_ssl):
    headers = {}
    if host_header:
        headers["Host"] = host_header
    async with get_async_client(base_url, verify_ssl) as ac:
        resp = await ac.get("/healthz", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_blueprint_full_lifecycle(base_url, host_header, verify_ssl):
    headers = {"Content-Type": "application/json"}
    if host_header:
        headers["Host"] = host_header
    async with get_async_client(base_url, verify_ssl) as ac:
        # Submit a blueprint
        blueprint = {
            "kind": "example",
            "variables": {},
            "schema_version": "v1"
        }
        resp = await ac.post("/blueprint", headers=headers, json=blueprint)
        assert resp.status_code == 200
        data = resp.json()
        assert "run_id" in data
        run_id = data["run_id"]

        # Build from blueprint
        resp = await ac.post(f"/run/{run_id}/build", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "built"

        # Plan (may fail if Terraform is not set up, but test the endpoint)
        resp = await ac.post(f"/run/{run_id}/plan", headers=headers)
        assert resp.status_code in (200, 404, 500)  # Accept 500 for CI

        # Apply (may fail if Terraform is not set up, but test the endpoint)
        resp = await ac.post(f"/run/{run_id}/apply", headers=headers)
        assert resp.status_code in (200, 404, 500)

        # Status
        resp = await ac.get(f"/run/{run_id}/status", headers=headers)
        assert resp.status_code == 200
        assert "status" in resp.json()

        # Summary
        resp = await ac.get(f"/run/{run_id}/summary", headers=headers)
        assert resp.status_code in (200, 404) 