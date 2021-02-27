"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import Any, Union

# standard libraries
import os
import sys
import re

# internal libraries
from ...core.error import AutoError
from ...core.logging import printer
from ...core.parallel import single 
from ...core.progress import get_bar
from ...core.stream import Instructions, mail
from ...library.create_xdmf import create_xdmf
from ...resources import CONFIG, DEFAULTS

# define public interface
__all__ = ['xdmf', ]

# define default constants (public)
GRID: str = DEFAULTS['general']['files']['grid']
HIGH: int = DEFAULTS['create']['xdmf']['high']
LOW: int = DEFAULTS['create']['xdmf']['low']
OUT: str = DEFAULTS['general']['files']['output']
PLOT: str = DEFAULTS['general']['files']['plot']
SKIP: int = DEFAULTS['create']['xdmf']['skip']

# define default and configuration constants (internal)
STR_INCLUDE = re.compile(DEFAULTS['general']['files']['plot'])
STR_EXCLUDE = re.compile(DEFAULTS['general']['files']['forced'])
BAR_SWITCH = CONFIG['create']['xdmf']['switch']

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # determine arguments passed
    if args.get('auto', False):
        range_given = False
        files_given = False
        bname_given = False
    else:    
        range_given = any(args.get(key, False) for key in ('low', 'high', 'skip'))
        files_given = 'files' in args.keys()
        bname_given = 'basename' in args.keys()
    
    # resolve proper absolute directory paths
    args['path'] = os.path.realpath(os.path.expanduser(args['path']))
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))
    source = args['path']

    # prepare conditions in order to arrange a list of files to process
    if (not files_given and not range_given) or not bname_given:
        listdir = os.listdir(source)
        condition = lambda file: re.search(STR_INCLUDE, file) and not re.search(STR_EXCLUDE, file)

    # create the filelist (throw if not defaults present)
    low: int = args['low']
    high: int = args['high']
    skip: int = args['skip']
    files: Union[range, list[int]] 
    if not files_given: 
        if range_given:
            high = high + 1
            files = range(low, high, skip)
            args['message'] = f'range({low}, {high}, {skip})'
        else:
            files = sorted([int(file[-4:]) for file in listdir if condition(file)])
            args['message'] = f'[{",".join(str(f) for f in files[:(min(5, len(files)))])}{", ..." if len(files) > 5 else ""}]'
            if not files:
                raise AutoError(f'Cannot automatically identify simulation files on path {source}')
        args['files'] = files
    else:
        files = args['files']
        args['message'] = f'[{",".join(str(f) for f in files)}]'

    # create the basename
    if not bname_given:
        try:
            args['basename'], *_ = next(filter(condition, (file for file in listdir))).split(STR_INCLUDE.pattern)
        except StopIteration:
            raise AutoError(f'Cannot automatically parse basename for simulation files on path {source}')
    
    return args

def attach_context(**args: Any) -> dict[str, Any]:
    """Provide a usefull progress bar if appropriate; with throw if some defaults missing."""
    if len(args['files']) >= BAR_SWITCH and sys.stdout.isatty():
        args['context'] = get_bar()
    else:
        args['context'] = get_bar(null=True)
        printer.info('Writing xdmf data out to file ...')
    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    basename: str = args['basename']
    dest: str = args['dest']
    files: list[int] = args['files']
    grid: str = args['grid']
    out: str = args['out']
    plot: str = args['plot']
    source: str = args['path']
    msg_files: str = args.pop('message')
    source = os.path.relpath(source)
    dest = os.path.relpath(dest)
    message = '\n'.join([
        f'Creating xdmf file from {len(files)} simulation files',
        f'  plotfiles = {source}/{basename}{plot}xxxx',
        f'  gridfiles = {source}/{basename}{grid}xxxx',
        f'  xdmf_file = {dest}/{basename}{out}.xmf',
        f'       xxxx = {msg_files}',
        f'',
        ])
    printer.info(message)
    return args

# define constants for handling the argument stream
PACKAGES = {'auto', 'basename', 'dest', 'files', 'grid', 'high', 'low', 'out', 'path', 'plot', 'skip'}
ROUTE = ('create', 'xdmf')
PRIORITY = {'ignore'}
CRATES = (adapt_arguments, log_messages, attach_context)
DROPS = {'auto', 'high', 'ignore', 'low', 'skip'}
MAPPING = {'grid': 'gridname', 'out': 'filename', 'plot': 'plotname', 'path': 'source'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

def xdmf(**arguments: Any) -> None:
    """Python application interface for creating xdmf from command line or python code.

    Keyword arguments:  
    basename: str Basename for flash simulation, will be guessed if not provided
                  (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)
    low: int      Begining number for timeseries hdf5 files; defaults to {LOW}.
    high: int     Ending number for timeseries hdf5 files; defaults to {HIGH}.
    skip: int     Number of files to skip for timeseries hdf5 files; defaults to {SKIP}.
    files: list   List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
    path: str     Path to timeseries hdf5 simulation output files; defaults to cwd.
    dest: str     Path to xdmf (contains relative paths to sim data); defaults to cwd.
    out: str      Output XDMF file name follower; defaults to a footer '{OUT}'.
    plot: str     Plot/Checkpoint file(s) name follower; defaults to '{PLOT}'.
    grid: str     Grid file(s) name follower; defaults to '{GRID}'.
    ignore: bool  Ignore configuration file provided arguments, options, and flags.
    auto: bool    Force behavior to attempt guessing BASENAME and [--files LIST].

    notes:  If neither BASENAME nor either of [LOW/HIGH/SKIP] or -f is specified,
            the PATH will be searched for flash simulation files and all
            such files identified will be used in sorted order.\
    """
    create_xdmf(**process_arguments(**arguments))
