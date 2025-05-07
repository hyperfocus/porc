import pytest
import os

def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default="http://test",
        help="Base URL for API tests"
    )
    parser.addoption(
        "--host-header",
        action="store",
        default=None,
        help="Custom Host header for API tests"
    )
    parser.addoption(
        "--ignore-ssl",
        action="store_true",
        default=False,
        help="Ignore SSL certificate verification"
    )

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # These should be set in the CI environment or local .env file
    required_vars = ["STORAGE_ACCOUNT", "STORAGE_ACCESS_KEY", "STORAGE_BUCKET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")
    yield

@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url")

@pytest.fixture
def host_header(request):
    return request.config.getoption("--host-header")

@pytest.fixture
def verify_ssl(request):
    return not request.config.getoption("--ignore-ssl") 