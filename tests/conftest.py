"""Supporting pytest fixtures for FlashKit testing."""

# standard libraries
import os
from pathlib import Path

# external libraries
import pytest

# internal libraries
from .support import exclude

@pytest.fixture(scope='session')
def testing(tmpdir_factory):
    """Create the temporary directory for all testing."""
    return Path(tmpdir_factory.getbasetemp())

@pytest.fixture(scope='session')
def scratch(testing):
    """Create the temporary directory for testing which needs a blank space."""
    scratch = testing.joinpath('scratch')
    scratch.mkdir()
    return scratch

@pytest.fixture(scope='session')
def example(testing):
    """Create the temporary directory for testing which requires a prototypical space."""
    example = testing.joinpath('example')
    example.mkdir()
    return example

@pytest.fixture(scope='session')
def reference():
    return Path('../FlashSupport/example')

@pytest.fixture(scope='session')
def loaded(example, reference):
    """Create equivalent working directory (with symlinks for files)."""
    for (path, folders, files) in os.walk(reference):
        working = Path(path)
        partial = os.path.relpath(working, reference) 
        if not exclude(working):
            for folder in folders:
                source = working.joinpath(folder)
                ending = example.joinpath(partial, folder).resolve()
                if not exclude(source): ending.mkdir()
            for file in files:
                source = working.joinpath(file)
                ending = example.joinpath(partial, file).resolve()
                if not exclude(source): ending.symlink_to(source.resolve())
