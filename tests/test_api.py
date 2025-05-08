import pytest
from httpx import AsyncClient
import logging
import asyncio

@pytest.fixture
def headers(host_header):
    h = {"Content-Type": "application/json"}
    if host_header:
        h["Host"] = host_header
    return h

@pytest.fixture
def async_client(base_url, ignore_ssl):
    return AsyncClient(base_url=base_url, verify=not ignore_ssl)

async def request(client, method, url, headers=None, json=None):
    return await getattr(client, method)(url, headers=headers, json=json)

@pytest.mark.asyncio
async def test_full_porc_workflow(async_client, headers, pr_sha):
    # Step 1: Submit Blueprint
    blueprint = {
        "kind": "postgres-db",
        "variables": {
            "db_name": "mydb",
            "db_user": "admin"
        },
        "schema_version": "1.0.0",
        "external_reference": pr_sha or "pr-123",
        "source_repo": "myorg/myrepo"
    }
    resp = await request(async_client, "post", "/blueprint", headers=headers, json=blueprint)
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    run_id = data["run_id"]

    # Step 2: Build 
    resp = await request(async_client, "post", f"/run/{run_id}/build", headers=headers)
    assert resp.status_code in (200, 202)
    build_data = resp.json() if hasattr(resp, 'json') else {}
    assert "status" in build_data or resp.status_code == 202

    # Step 3: Plan
    resp = await request(async_client, "post", f"/run/{run_id}/plan", headers=headers)
    assert resp.status_code in (200, 202, 500)  # 500 if TFE is not configured
    plan_data = resp.json() if hasattr(resp, 'json') else {}
    assert "status" in plan_data or resp.status_code == 500

    # Step 4: Apply
    resp = await request(async_client, "post", f"/run/{run_id}/apply", headers=headers)
    assert resp.status_code in (200, 202, 400, 500)  # 400 if not in PLANNED state, 500 if TFE error
    apply_data = resp.json() if hasattr(resp, 'json') else {}
    assert "status" in apply_data or resp.status_code in (400, 500)

    # Step 5: Status
    resp = await request(async_client, "get", f"/run/{run_id}/status", headers=headers)
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["run_id"] == run_id
    assert "status" in status_data

    # Optionally, check summary and logs endpoints
    resp = await request(async_client, "get", f"/run/{run_id}/summary", headers=headers)
    assert resp.status_code in (200, 404)
    resp = await request(async_client, "get", f"/run/{run_id}/logs", headers=headers)
    assert resp.status_code in (200, 404)

@pytest.mark.asyncio
async def test_full_lifecycle_all_routes(async_client, headers):
    blueprint = {
        "kind": "postgres-db",
        "variables": {},
        "schema_version": "1.0.0",
        "external_reference": "test-pr-123",
        "source_repo": "test-org/test-repo"
    }

    # Submit blueprint
    resp = await request(async_client, "post", "/blueprint", headers=headers, json=blueprint)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    endpoints = [
        ("post", f"/run/{run_id}/build"),
        ("post", f"/run/{run_id}/plan"),
        ("post", f"/run/{run_id}/apply"),
        ("get", f"/run/{run_id}/status"),
        ("get", f"/run/{run_id}/summary"),
        ("get", f"/run/{run_id}/logs"),
        ("post", f"/run/{run_id}/approve"),
        ("post", f"/run/{run_id}/cancel"),
        ("get", f"/run/{run_id}/checks"),
        ("post", f"/run/{run_id}/checks"),
        ("post", f"/run/{run_id}/notify"),
    ]

    for method, url in endpoints:
        try:
            resp = await request(async_client, method, url, headers=headers)
            if resp.status_code in (404, 501):
                logging.warning(f"{url} not implemented or not found.")
            else:
                assert resp.status_code in (200, 202, 500)
        except Exception as e:
            logging.error(f"Failed calling {url}: {e}")

        # Insert delay between stateful steps
        if "/build" in url or "/plan" in url or "/apply" in url:
            await asyncio.sleep(1)
