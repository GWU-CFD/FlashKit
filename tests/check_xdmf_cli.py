"""Testing the cli for xdmf operation."""

# standard libraries
import os
from functools import partial
from unittest.mock import patch

# external libraries
import pytest
from hypothesis import given, strategies
from cmdkit.app import ExitStatus 

# internal libraries
from flashkit.cli import main
from flashkit.cli.create import xdmf

STATUS = ExitStatus()

# define property testing strategies
bools = strategies.booleans()
naturals = strategies.integers(min_value=0)
lists = strategies.lists(naturals, min_size=1)
words = strategies.text(min_size=1, alphabet=strategies.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd', ), 
    blacklist_characters=('/')))

@pytest.fixture(scope='module')
def mocked(module_mocker):
    """Supporting mock facilities for cli testing."""
    module_mocker.spy(xdmf, 'xdmf')
    module_mocker.patch('flashkit.cli.create.xdmf.xdmf', return_value=None)
    return module_mocker

@pytest.mark.cli
def check_xdmf_help():
    """Verify that help message works properly."""
    assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf --help'))
    assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf -h'))

@pytest.mark.cli
def check_xdmf_version():
    """Verify that help message works properly."""
    assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf --version'))
    assert STATUS.success == os.WEXITSTATUS(os.system('flashkit create xdmf -v'))

@pytest.mark.cli
def check_xdmf_noargs():
    """Verify that usage message is not used; fails in root dir."""
    assert STATUS.runtime_error == os.WEXITSTATUS(os.system('flashkit create xdmf'))

@pytest.mark.cli
def check_xdmf_badargs():
    """Verify that bad args fails with correct exit status."""
    assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf --bob'))
    assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf -w'))
    assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf -f"1/2"'))
    assert STATUS.bad_argument == os.WEXITSTATUS(os.system('flashkit create xdmf -b1.2'))

@pytest.mark.cli
@given(basename=words, low=naturals, high=naturals, skip=naturals, files=lists,
       path=words, dest=words, out=words, plot=words, grid=words, force=words,
       auto=bools, find=bools, ignore=bools)
def check_xdmf_options(basename, low, high, skip, files,path, dest, out, plot, grid, force, auto, find, ignore, mocked):
    """Verify that the expected cli options work properly."""
    
    expected = {'basename': basename, 'low': low, 'high': high, 'skip': skip, 'files': files,
                'path': path, 'dest': dest, 'out': out, 'plot': plot, 'grid': grid, 'force': force,
                'ignore': ignore, 'auto': auto, 'find': find}

    # test short form of arguments
    _files = ','.join(str(f) for f in files)
    _ignore = '-I ' if ignore else ''
    _auto = '-A ' if auto else ''
    _find = '-B ' if find else ''
    provided = f'{basename} -b{low} -e{high} -s{skip} -f{_files} ' \
               f'-p{path} -d{dest} -o{out} -c{plot} -g{grid} -q{force} ' \
               f'{_ignore}{_auto}{_find}'.split()
    with patch('sys.argv', ['flashkit', 'create', 'xdmf'] + provided):
        assert STATUS.success == main()
        xdmf.xdmf.assert_called_with(**expected)
    
    # test long form of arguments
    _files = ','.join(str(f) for f in files)
    _ignore = '--ignore ' if ignore else ''
    _auto = '--auto ' if auto else ''
    _find = '--find ' if find else ''
    provided = f'{basename} --low {low} --high {high} --skip {skip} --files {_files} ' \
               f'--path {path} --dest {dest} --out {out} --plot {plot} --grid {grid} --force {force} ' \
               f'{_ignore}{_auto}{_find}'.split()
    with patch('sys.argv', ['flashkit', 'create', 'xdmf'] + provided):
        assert STATUS.success == main()
        xdmf.xdmf.assert_called_with(**expected)
