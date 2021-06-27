"""Testing the cli for xdmf operation."""

# type annotations
from typing import NamedTuple

# standard libraries
import os

# external libraries
import pytest
from cmdkit.app import ExitStatus 

# internal libraries
from .support import change_directory
from flashkit.cli import main
from flashkit.cli.create import xdmf

STATUS = ExitStatus()

class Case(NamedTuple):
    """Useful tuple of test cases definition."""
    provided: list
    expected: dict

@pytest.fixture()
def case_default():
    """Define the default case for the xdmf cli."""
    return Case(
            provided=[],
            expected={
                'plot': None,
                'basename': None,
                'low': None,
                'path': None,
                'files': None,
                'grid': None,
                'ignore': False,
                'skip': None,
                'auto': False,
                'high': None,
                'dest': None,
                'out': None
                })

@pytest.fixture()
def case_short():
    """Define the short option case for the xdmf cli."""
    return Case(
            provided=[
                'INS_LidDr_Cavity',
                '-b5', '-e15', '-s3','-f1,2,3,4,5',
                '-psource', '-ddest', '-o_paraview',
                '-i_hdf5_chk_', '-g_hdf5_geometry_',
                '-I', '-A',
                ],
            expected={
                'plot': '_hdf5_chk_',
                'basename': 'INS_LidDr_Cavity',
                'low': 5,
                'path': 'source',
                'files': [1,2,3,4,5],
                'grid': '_hdf5_geometry_',
                'ignore': True,
                'skip': 3,
                'auto': True,
                'high': 15,
                'dest': 'dest',
                'out': '_paraview',
                })

@pytest.fixture()
def case_long():
    """Define the long option case for the xdmf cli."""
    return Case(
            provided=[
                'INS_LidDr_Cavity',
                '--low', '5', '--high', '15', '--skip', '3', '--files', '1,2,3,4,5',
                '--path', 'source', '--dest', 'dest', '--out', '_paraview',
                '--plot', '_hdf5_chk_', '--grid', '_hdf5_geometry_',
                '--ignore', '--auto',
                ],
            expected={
                'plot': '_hdf5_chk_',
                'basename': 'INS_LidDr_Cavity',
                'low': 5,
                'path': 'source',
                'files': [1,2,3,4,5],
                'grid': '_hdf5_geometry_',
                'ignore': True,
                'skip': 3,
                'auto': True,
                'high': 15,
                'dest': 'dest',
                'out': '_paraview',
                })

@pytest.fixture(params=[
    pytest.lazy_fixture('case_default'),
    pytest.lazy_fixture('case_short'),
    pytest.lazy_fixture('case_long'),
    ])
def data(request):
    """Parameterized data for testing xdmf cli."""
    return request.param

@pytest.mark.cli
def check_xdmf_help(scratch):
    """Verify that help message works properly."""
    with change_directory(scratch):
        assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf --help'))
        assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf -h'))

@pytest.mark.cli
def check_xdmf_version(scratch):
    """Verify that help message works properly."""
    with change_directory(scratch):
        assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf --version'))
        assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf -v'))

@pytest.mark.cli
def check_xdmf_noargs(scratch):
    """Verify that usage message is not used; fails in root dir."""
    with change_directory(scratch):
        assert STATUS.runtime_error == os.WEXITSTATUS(os.system('flashkit create xdmf'))

@pytest.mark.cli
def check_xdmf_badargs(scratch):
    """Verify that bad args fails with correct exit status."""
    with change_directory(scratch):
        assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf --bob'))
        assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf -w'))
        assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf -f"1/2"'))
        assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf -b1.2'))

@pytest.mark.cli
def check_xdmf_options(scratch, data, mocker):
    """ Verify that the expected cli options work properly."""

    # instrument desired functions
    mocker.patch('sys.argv', ['flashkit', 'create', 'xdmf'] + data.provided)
    mocker.spy(xdmf, 'xdmf')

    with change_directory(scratch):
        assert STATUS.runtime_error == main()
        xdmf.xdmf.assert_called_with(**data.expected)
