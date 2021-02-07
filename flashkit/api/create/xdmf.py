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
from ...core import stream
from ...resources import CONFIG, DEFAULTS

# external libraries
from alive_progress import alive_bar, config_handler

# define public interface
__all__ = ['xdmf', ]

# default constants
STR_INCLUDE = re.compile(DEFAULTS['general']['files']['plot'])
STR_EXCLUDE = re.compile(DEFAULTS['general']['files']['forced'])
BAR_SWITCH_XDMF = CONFIG['create']['xdmf']['switch']
LABELS = ('auto', 'basename', 'dest', 'files', 'grid', 'high', 'low', 'out', 'path', 'plot', 'skip')
PRIORITY = {'ignore', }
RANGES = ('low', 'high', 'skip') 
ROUTE = ('create', 'xdmf')
TRANSLATE = {'grid': 'gridname', 'out': 'filename', 'plot': 'plotname', 'path': 'source'}
UNLOAD = {'auto', 'high', 'low', 'skip'}

def xdmf(**arguments: Dict[str, Any]) -> None:
    """Buisness logic for creating xdmf from command line or python code.

    Keyword arguments:  
    basename: str Basename for flash simulation, will be guessed if not provided
                  (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)
    low:  int     Begining number for timeseries hdf5 files; defaults to {LOW}.
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
    dispatch(**arguments)

def adapt_arguments(**args: Dict[str, Any]) -> Dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults is corrupted."""

    # determine arguments passed
    if args.get('auto', False):
        range_given = False
        files_given = False
        bname_given = False
    else:    
        range_given = any(args.get(key, False) for key in RANGES)
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
    low, high, skip = (args.get(key) for key in RANGES)
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

def attach_context(**args: Dict[str, Any]) -> Dict[str, Any]:
    """Provide a usefull progress bar if appropriate; with throw if defaults corrupted."""
    if len(args['files']) >= BAR_SWITCH_XDMF and sys.stdout.isatty():
        config_handler.set_global(theme='smooth', unknown='horizontal')
        args['context'] = alive_bar
    else:
        print('\nWriting xdmf data out to file ...')
    return args

def log_messages(**args: Dict[str, Any]) -> Dict[str, Any]:
    """Log screen messages to logger; will throw if defaults corrupted."""
    labels = ('basename', 'dest', 'files', 'grid', 'out', 'plot', 'path')
    basename, dest, files, grid, out, plot, source = (args.get(key) for key in labels)
    msg_files = args.pop('message', '')
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
    print(message)
    return args

@stream.ship_clean(LABELS, ROUTE, PRIORITY)
@stream.straps((adapt_arguments, log_messages, attach_context))
@stream.prune(UNLOAD, TRANSLATE)
def dispatch(**args):
    """Dispatch transformed args to library method."""
    create_xdmf.file(**args)
