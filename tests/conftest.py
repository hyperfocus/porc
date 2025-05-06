def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default="http://test",
        help="Base URL for API tests"
    )

import pytest

@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url") 