import pytest
from httpx import AsyncClient
from porc_api.main import app

@pytest.mark.asyncio
async def test_healthz(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_blueprint_lifecycle(base_url):
    # Submit a blueprint
    blueprint = {
        "kind": "example",
        "variables": {},
        "schema_version": "v1"
    }
    async with AsyncClient(app=app, base_url=base_url) as ac:
        resp = await ac.post("/blueprint", json=blueprint)
        assert resp.status_code == 200
        data = resp.json()
        assert "run_id" in data
        run_id = data["run_id"]

        # Build from blueprint
        resp = await ac.post(f"/run/{run_id}/build")
        assert resp.status_code == 200
        assert resp.json()["status"] == "built"

        # Plan (may fail if Terraform is not set up, but test the endpoint)
        resp = await ac.post(f"/run/{run_id}/plan")
        assert resp.status_code in (200, 404)  # 404 if run dir not found

        # Apply (same as above)
        resp = await ac.post(f"/run/{run_id}/apply")
        assert resp.status_code in (200, 404)

        # Status
        resp = await ac.get(f"/run/{run_id}/status")
        assert resp.status_code == 200
        assert "status" in resp.json()

        # Summary
        resp = await ac.get(f"/run/{run_id}/summary")
        assert resp.status_code in (200, 404)

@pytest.mark.asyncio
async def test_invalid_run_id(base_url):
    async with AsyncClient(app=app, base_url=base_url) as ac:
        # Test endpoints with an invalid run_id
        invalid_id = "../../etc/passwd"
        for endpoint in [
            f"/run/{invalid_id}/build",
            f"/run/{invalid_id}/plan",
            f"/run/{invalid_id}/apply",
            f"/run/{invalid_id}/status",
            f"/run/{invalid_id}/summary",
        ]:
            resp = await ac.post(endpoint) if "plan" in endpoint or "apply" in endpoint or "build" in endpoint else await ac.get(endpoint)
            assert resp.status_code == 400
            assert resp.json()["error"] == "Invalid run_id" 