import pytest

@pytest.fixture(scope='session')
def api_dir(tmpdir_factory):
    """Create the temporary directory for api testing."""
    return tmpdir_factory.getbasetemp().mkdir('api')
