import pytest

@pytest.fixture(scope='session')
def testing(tmpdir_factory):
    """Create the temporary directory for all testing."""
    return tmpdir_factory.getbasetemp()

@pytest.fixture(scope='session')
def scratch(testing):
    """Create the temporary directory for testing which needs a blank space."""
    return testing.mkdir('scratch')

@pytest.fixture(scope='session')
def example(testing):
    """Create the temporary directory for testing which requires a prototypical space."""
    return testing.mkdir('example')
