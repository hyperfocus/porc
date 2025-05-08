import pytest
import os
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
    parser.addoption(
        "--pr-id",
        default=None,
        help="GitHub PR number",
        action="store",
    )
    parser.addoption(
        "--pr-sha",
        default=None,
        help="GitHub PR commit SHA",
        action="store",
    )

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Store original environment variables
    original_env = {
        'STORAGE_BUCKET': os.getenv('STORAGE_BUCKET'),
        'STORAGE_ACCOUNT': os.getenv('STORAGE_ACCOUNT'),
        'STORAGE_ACCESS_KEY': os.getenv('STORAGE_ACCESS_KEY')
    }
    
    # Set test environment variables
    os.environ['STORAGE_BUCKET'] = 'porcbundles'
    os.environ['STORAGE_ACCOUNT'] = 'porcbundles'
    os.environ['STORAGE_ACCESS_KEY'] = 'test-key'
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

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
def pr_id(request):
    return request.config.getoption("--pr-id")

@pytest.fixture
def pr_sha(request):
    return request.config.getoption("--pr-sha")

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app) 