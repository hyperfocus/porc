import pytest

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

@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url")

@pytest.fixture
def host_header(request):
    return request.config.getoption("--host-header")

@pytest.fixture
def verify_ssl(request):
    return not request.config.getoption("--ignore-ssl") 