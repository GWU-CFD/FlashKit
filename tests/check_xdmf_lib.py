"""Testing the library implementation of xdmf."""

# type annotations
from __future__ import annotations
from typing import NamedTuple

# standard libraries
import os
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
    expected: list[str]
    excluded: list[str]

@pytest.fixture(params=[

    ], ids=[])
def data(request, example, loaded):
    """Parameterized setup for xdmf feature tests."""
    case = request.param
    working = example.joinpath(case.folder)
    with change_directory(working):
        os.system('flashkit create xdmf --ignore ' + case.options)
    return case

@pytest.mark.lib
def check_xdmf(example):
    """Verify that the output matches the intent."""
    pass 
