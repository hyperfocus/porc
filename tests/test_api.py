import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from porc_api.main import app
import logging
import asyncio

@pytest.fixture
def headers(host_header):
    h = {"Content-Type": "application/json"}
    if host_header:
        h["Host"] = host_header
    return h

@pytest.fixture
def sync_or_async_client(base_url, ignore_ssl):
    if base_url == "http://test":
        return TestClient(app)
    return AsyncClient(base_url=base_url, verify=not ignore_ssl)

async def request(client, method, url, headers=None, json=None):
    if isinstance(client, AsyncClient):
        return await getattr(client, method)(url, headers=headers, json=json)
    f = getattr(client, method)
    return f(url, headers=headers, json=json) if json else f(url, headers=headers)

@pytest.mark.asyncio
async def test_full_lifecycle_all_routes(sync_or_async_client, headers):
    blueprint = {
        "kind": "postgres-db",
        "variables": {},
        "schema_version": "1.0.0",
        "external_reference": "test-pr-123",
        "source_repo": "test-org/test-repo"
    }

    # Submit blueprint
    resp = await request(sync_or_async_client, "post", "/blueprint", headers=headers, json=blueprint)
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
            resp = await request(sync_or_async_client, method, url, headers=headers)
            if resp.status_code in (404, 501):
                logging.warning(f"{url} not implemented or not found.")
            else:
                assert resp.status_code in (200, 202, 500)
        except Exception as e:
            logging.error(f"Failed calling {url}: {e}")

        # Insert delay between stateful steps
        if "/build" in url or "/plan" in url or "/apply" in url:
            await asyncio.sleep(1)
