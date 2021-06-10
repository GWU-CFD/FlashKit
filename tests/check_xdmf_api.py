"""Testing the api for xdmf operation."""

# standard libraries
import os
import re

from typing import NamedTuple

# internal libraries
from flashkit.api.create import _xdmf
from flashkit.core.progress import get_bar
from flashkit.resources import CONFIG, DEFAULTS

# external libraries
import pytest

# define default and config constants
FILES = DEFAULTS['general']['files']
XDMF = DEFAULTS['create']['xdmf']
SWITCH = CONFIG['create']['xdmf']['switch']

class Case(NamedTuple):
    """Useful tuple of test cases definition."""
    provided: dict
    expected: dict

@pytest.fixture(scope='module')
def working(api_dir):
    """Create the files needed for xdmf api testing."""
    
    # working directory for testing
    xdmf_dir = api_dir.mkdir('xdmf')

    # a set of plot files
    xdmf_dir.join('INS_LidDr_Cavity_hdf5_grd_0000').write('')
    xdmf_dir.join('INS_LidDr_Cavity_hdf5_plt_cnt_0000').write('')
    xdmf_dir.join('INS_LidDr_Cavity_hdf5_plt_cnt_0001').write('')
    xdmf_dir.join('INS_LidDr_Cavity_hdf5_plt_cnt_0002').write('')
    
    # a second (salt) set of plot files
    xdmf_dir.join('INS_XxAddSalt_hdf5_grd_0000').write('')
    xdmf_dir.join('INS_XxAddSalt_hdf5_plt_cnt_0010').write('')
    xdmf_dir.join('INS_XxAddSalt_hdf5_plt_cnt_0011').write('')
    xdmf_dir.join('INS_XxAddSalt_hdf5_plt_cnt_0012').write('')
    xdmf_dir.join('INS_LidDr_Cavity_forced_hdf5_plt_cnt_0000').write('')
    
    # a set of checkpoint files
    xdmf_dir.join('INS_Rayleigh_hdf5_geometry_0000').write('')
    xdmf_dir.join('INS_Rayleigh_hdf5_chk_1000').write('')
    xdmf_dir.join('INS_Rayleigh_hdf5_chk_0200').write('')
    xdmf_dir.join('INS_Rayleigh_hdf5_chk_0030').write('')
    xdmf_dir.join('INS_Rayleigh_hdf5_chk_0004').write('')

    # a source and destination directory
    source_dir = xdmf_dir.mkdir('source')
    source_dir.join('INS_LidDr_Cavity_hdf5_grd_0000').write('')
    source_dir.join('INS_LidDr_Cavity_hdf5_plt_cnt_0000').write('')
    source_dir.join('INS_LidDr_Cavity_hdf5_plt_cnt_0005').write('')
    source_dir.join('INS_LidDr_Cavity_hdf5_plt_cnt_0010').write('')
    dest_dir = xdmf_dir.mkdir('dest')

    return xdmf_dir

@pytest.fixture()
def case_default(working):
    """Define the default case for the xdmf api."""
    return Case(
            provided={
                'ignore': True,
                },
            expected={
                'dest': str(working),
                'files': range(XDMF['low'], XDMF['high']+1, XDMF['skip']),
                'basename': 'INS_LidDr_Cavity',
                'context': get_bar(null=True),
                'gridname': FILES['grid'],
                'filename': FILES['output'],
                'plotname': FILES['plot'],
                'source': str(working),
                })

@pytest.fixture()
def case_auto(working):
    """Define the automatic case for the xdmf api."""
    return Case(
            provided={
                'ignore': True,
                'auto': True, 
                },
            expected={
                'dest': str(working),
                'files': [0, 1, 2],
                'basename': 'INS_LidDr_Cavity',
                'context': get_bar(null=True),
                'gridname': FILES['grid'],
                'filename': FILES['output'],
                'plotname': FILES['plot'],
                'source': str(working),
                })

@pytest.fixture()
def case_manual(working):
    """Define the manual names and files case for the xdmf api."""
    return Case(
            provided={
                'ignore': True,
                'basename': 'INS_Rayleigh',
                'files': [1000, 200, 30, 4],
                'grid': '_hdf5_geometry_',
                'plot': '_hdf5_chk_',
                'out': '_paraview'
                },
            expected={
                'dest': str(working),
                'files': [1000, 200, 30, 4],
                'basename': 'INS_Rayleigh',
                'context': get_bar(null=True),
                'gridname': '_hdf5_geometry_',
                'filename': '_paraview',
                'plotname': '_hdf5_chk_',
                'source': str(working),
                })

@pytest.fixture()
def case_paths(working):
    """Define the paths and range case for the xdmf api."""
    return Case(
            provided={
                'ignore': True,
                'low': 2,
                'high': 12,
                'skip': 5,
                'path': 'source',
                'dest': 'dest',
                },
            expected={
                'dest': str(working.join('dest')),
                'files': range(2, 13, 5),
                'basename': 'INS_LidDr_Cavity',
                'context': get_bar(null=True),
                'gridname': FILES['grid'],
                'filename': FILES['output'],
                'plotname': FILES['plot'],
                'source': str(working.join('source')),
                })

@pytest.fixture()
def case_context(working):
    """Define the context case for the xdmf api."""
    return Case(
            provided={
                'ignore': True,
                'files': list(range(0, SWITCH+2)),
                },
            expected={
                'dest': str(working),
                'files': list(range(0, SWITCH+2)),
                'basename': 'INS_LidDr_Cavity',
                'context': get_bar(),
                'gridname': FILES['grid'],
                'filename': FILES['output'],
                'plotname': FILES['plot'],
                'source': str(working),
                })

@pytest.fixture(params=[
    pytest.lazy_fixture('case_default'),
    pytest.lazy_fixture('case_auto'),
    pytest.lazy_fixture('case_manual'),
    pytest.lazy_fixture('case_paths'),
    pytest.lazy_fixture('case_context'),
    ])
def data(request):
    """Parameterized data for testing xdmf api."""
    return request.param

@pytest.mark.unit
@pytest.mark.api
def checking(working, data, mocker):

    # don't run library function or logging
    mocker.patch('flashkit.api.create._xdmf.create_xdmf', return_value=None)
    mocker.patch('flashkit.api.create._xdmf.printer.info', return_value=None)
    mocker.patch('flashkit.api.create._xdmf.sys.stdout.isatty', return_value=True)

    # instrument desired functions
    mocker.spy(_xdmf, 'create_xdmf')
    mocker.spy(_xdmf.printer, 'info')
    
    with working.as_cwd():
        _xdmf.xdmf(**data.provided)

        # check adapt_arguments and attached context
        _xdmf.create_xdmf.assert_called_with(**data.expected)
        
        # check attached context message
        if len(data.expected['files']) < SWITCH:
            _xdmf.printer.info.assert_any_call('Writing xdmf data out to file ...')

        # check logging
        found = False
        exp = data.expected
        files = exp['files']
        fmsgs = f'[{",".join(str(f) for f in files[:(min(5, len(files)))])}{", ..." if len(files) > 5 else ""}]'
        check = rf".*{len(data.expected['files'])}.*files.*" \
                rf".*{os.path.relpath(exp['source'])}/{exp['basename']}{exp['plotname']}xxxx.*" \
                rf".*{os.path.relpath(exp['source'])}/{exp['basename']}{exp['gridname']}xxxx.*" \
                rf".*{os.path.relpath(exp['dest'])}/{exp['basename']}{exp['filename']}.xmf.*" \
                rf".*{fmsgs}.*"
        for message, kwargs in _xdmf.printer.info.call_args_list:
            if re.search(check, message[0], flags=re.DOTALL):
                found = True
        assert found == True
