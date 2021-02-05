"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import Any, Dict 

# standard libraries
import os
import sys
import re

# internal libraries
from ...library import create_xdmf
from ...resources import CONFIG, DEFAULTS
from ...core import get_arguments, get_defaults

# external libraries
from alive_progress import alive_bar, config_handler

# define public interface
__all__ = ['xdmf', ]

# default constants
STR_INCLUDE = re.compile(DEFAULTS['general']['files']['plot'])
STR_EXCLUDE = re.compile(DEFAULTS['general']['files']['forced'])
BAR_SWITCH_XDMF = CONFIG['create']['xdmf']['switch']

def xdmf(**args: Dict[str, Any]) -> None:
    """Buisness logic for creating xdmf from command line or python code.

    Keyword arguments:  
    basename: str Basename for flash simulation, will be guessed if not provided
                  (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)
    low:  int     Begining number for timeseries hdf5 files; defaults to {LOW}.
    high: int     Ending number for timeseries hdf5 files; defaults to {HIGH}.
    skip: int     Number of files to skip for timeseries hdf5 files; defaults to {SKIP}.
    files: list   List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
    path: str     Path to timeseries hdf5 simulation output files; defaults to cwd.
    out: str      Output XDMF file name follower; defaults to a footer '{OUT}'.
    plot: str     Plot/Checkpoint file(s) name follower; defaults to '{PLOT}'.
    grid: str     Grid file(s) name follower; defaults to '{GRID}'.
    ignore         Ignore configuration file provided arguments, options, and flags.
    auto           Force behavior to attempt guessing BASENAME and [--files LIST].

    notes:  If neither BASENAME nor either of [LOW/HIGH/SKIP] or -f is specified,
            the PATH will be searched for flash simulation files and all
            such files identified will be used in sorted order.\
    """
    # upack switch options
    auto = args.get('auto', False)
    ignore = args.get('ignore', False)

    # determine if arguments passed
    range_given = any(args.get(key, False) for key in {'low', 'high', 'skip'})
    files_given = 'files' in args.keys()
    bname_given = 'basename' in args.keys()
        
    # package up the arguments for parsing defaults and config files
    options = {'basename', 'low', 'high', 'skip', 'files', 'path', 'out', 'plot', 'grid'}
    local = {key: args.get(key, None) for key in options}
    local = {'create': {'xdmf': {key: value for key, value in local.items() if value is not None}}} 
        
    # gather defaults and optionally use configuration files
    if ignore:
        arguments = get_defaults(local=local)['create']['xdmf']
    else:
        arguments = get_arguments(local=local)['create']['xdmf']
        
    # Update the assessment of argument existance
    range_given = any(arguments.get(key, False) for key in {'low', 'high', 'skip'})
    files_given = 'files' in arguments.keys()
    bname_given = 'basename' in arguments.keys()
        
    # force automatic if desired
    if auto:
        range_given = False
        file_given = False
        bname_given = False
        
    # unpack path argument (throw if not present)
    path = arguments['path']

    # prepare conditions in order to arrang a list of files to process
    if (not files_given and not range_given) or not bname_given:
        listdir = os.listdir(os.getcwd() + '/' + path + '')
        condition = lambda file: re.search(STR_INCLUDE, file) and not re.search(STR_EXCLUDE, file)

    # create the filelist (throw if not defaults present)
    low, high, skip = (arguments.pop(key) for key in ('low', 'high', 'skip'))
    if not files_given: 
        if range_given:
            high = high + 1
            files = range(low, high, skip)
            msg_files = f'range({low}, {high}, {skip})'
        else:
            files = sorted([int(file[-4:]) for file in listdir if condition(file)])
            msg_files = f'[{",".join(str(f) for f in files[:(min(5, len(files)))])}{", ..." if len(files) > 5 else ""}]'
            if not files:
                raise AutoError(f'Cannot automatically identify simulation files on path {path}')
    else:
        files = arguments['files']
        msg_files = f'[{",".join(str(f) for f in files)}]'

    # create the basename
    if not bname_given:
        try:
            basename, *_ = next(filter(condition, (file for file in listdir))).split(STR_INCLUDE.pattern)
        except StopIteration:
            raise AutoError(f'Cannot automatically parse basename for simulation files on path {path}')
    else:
        basename = arguments['basename']

    # unpack filenames (throw if not present)
    plot, grid, out = (arguments[key] for key in ('plot', 'grid', 'out'))

    # Prepare useful messages
    message = '\n'.join([
        f'Creating xdmf file from {len(files)} simulation files',
        f'  plotfiles = {path}{basename}{plot}xxxx',
        f'  gridfiles = {path}{basename}{grid}xxxx',
        f'  xdmf_file = {path}{basename}{out}.xmf',
        f'       xxxx = {msg_files}',
        f'',
        ])

    # Create xdmf file using core library; optionally w/ progress bar
    if len(files) >= BAR_SWITCH_XDMF and sys.stdout.isatty():
        config_handler.set_global(theme='smooth', unknown='horizontal')
        print(message)
        create_xdmf.file(files=files, basename=basename, path=path, filename=out, 
                         plotname=plot, gridname=grid, context=alive_bar)
    else:
        message += '\nWriting xdmf data out to file ...'
        print(message)
        create_xdmf.file(files=files, basename=basename, path=path, filename=out, 
                         plotname=plot, gridname=grid)
