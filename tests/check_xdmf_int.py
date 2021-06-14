"""Testing the integration of xdmf operations."""

# type annotations
from typing import NamedTuple

# standard libraries
import os
from difflib import unified_diff
from pathlib import Path

# exernal libraries
import pytest

# internal libraries
from .support import change_directory

class Case(NamedTuple):
    """Useful tuple of test cases definition."""
    folder: str
    options: str
    output: str

@pytest.fixture(params=[
    Case('test/lidcavity/pm', '--auto', 'INS_LidDr_Cavity.xmf'),
    Case('test/lidcavity/ug', '--auto', 'INS_LidDr_Cavity.xmf'),
    ])
def data(request, example, loaded):
    """Parameterized setup for xdmf integration tests."""
    case = request.param
    working = example.joinpath(case.folder)
    with change_directory(working):
        os.system('flashkit create xdmf ' + case.options)
    return Path(case.folder).joinpath(case.output)

@pytest.mark.int
def checking(example, reference, data):
    """Verify that the output exactly matches the reference."""
    checking = example.joinpath(data)
    standard = reference.joinpath(data)
    with open(checking) as chk, open(standard) as std:
        diff = list(unified_diff(std.readlines(), chk.readlines()))
        same = not diff
        assert same, ''.join(diff[2:])
