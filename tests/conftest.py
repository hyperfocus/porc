import pytest
from fastapi.testclient import TestClient
from porc_api.main import app

def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API",
        action="store",
    )
    parser.addoption(
        "--host-header",
        default="localhost:8000",
        help="Host header for the API",
        action="store",
    )
    parser.addoption(
        "--ignore-ssl",
        default=False,
        help="Ignore SSL verification",
        action="store_true",
    )

@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url")

@pytest.fixture
def host_header(request):
    return request.config.getoption("--host-header")

@pytest.fixture
def ignore_ssl(request):
    return request.config.getoption("--ignore-ssl")

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app) 