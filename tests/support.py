"""Supporting methods for FlashKit testing."""

# standard libraries
import contextlib
import os
import re
from pathlib import Path

@contextlib.contextmanager
def change_directory(path):
    """Changes working directory and returns to previous on exit."""
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)

def exclude(path: str):
    """Does the path meet any rules for exclusion?"""
    EXCLUDES = {r'__.*__', r'/\.'}
    NO_LINKS = {r'\.xmf', r'\.h5', 'run'}
    return any(re.search(exclude, str(path)) for exclude in EXCLUDES.union(NO_LINKS))

