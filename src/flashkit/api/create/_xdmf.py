"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import Any, Union

# standard libraries
import logging
import os
import re
import sys

# internal libraries
from ...core.error import AutoError
from ...core.parallel import safe, single 
from ...core.progress import attach_context
from ...core.stream import Instructions, mail
from ...library.create_xdmf import create_xdmf
from ...resources import CONFIG, DEFAULTS

# define public interface
__all__ = ['xdmf', ]

logger = logging.getLogger(__name__)

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # determine arguments passed
    if args.get('auto', False):
        range_given = False
        files_given = False
        bname_given = False
    else:
        if args.get('find', False):
            range_given = False
            files_given = False
        else:
            range_given = any(args.get(key, False) for key in ('low', 'high', 'skip'))
            files_given = 'files' in args.keys()
        bname_given = 'basename' in args.keys()
    
    # resolve proper absolute directory paths
    args['path'] = os.path.realpath(os.path.expanduser(args['path']))
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))
    source = args['path']

    # prepare conditions in order to arrange a list of files to process
    str_include = re.compile(args['plot'])
    str_exclude = re.compile(args['force'])
    if (not files_given and not range_given) or not bname_given:
        listdir = os.listdir(source)
        orig_cond = lambda file: re.search(str_include, file) and not re.search(str_exclude, file)

    # create the basename
    if not bname_given:
        try:
            args['basename'], *_ = next(filter(orig_cond, (file for file in listdir))).split(str_include.pattern)
        except StopIteration:
            raise AutoError(f'Cannot automatically parse basename for simulation files on path {source}')
    full_cond = lambda file: orig_cond(file) and re.search(re.compile(args['basename']), file)
    
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
            files = sorted([int(file[-4:]) for file in listdir if full_cond(file)])
            args['message'] = f'[{",".join(str(f) for f in files[:(min(5, len(files)))])}{", ..." if len(files) > 5 else ""}]'
            if files is None:
                raise AutoError(f'Cannot automatically identify simulation files on path {source}')
        args['files'] = files
    else:
        files = args['files']
        args['message'] = f'[{",".join(str(f) for f in files)}]'

    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    basename = args['basename']
    dest = os.path.relpath(args['dest'])
    source = os.path.relpath(args['path'])
    files = args['files']
    grid = args['grid']
    out = args['out']
    plot = args['plot']
    msg_files = args.pop('message')
    message = '\n'.join([
        f'\nCreating xdmf file from {len(files)} simulation files',
        f'  plotfiles = {source}/{basename}{plot}xxxx',
        f'  gridfiles = {source}/{basename}{grid}xxxx',
        f'  xdmf_file = {dest}/{basename}{out}.xmf',
        f'       xxxx = {msg_files}',
        f'',
        f'Writing xdmf data out to file ...',
        ])
    logger.info(message)
    return args

# define constants for handling the argument stream
PACKAGES = {'auto', 'basename', 'dest', 'files', 'find', 'force', 'grid', 'high', 'low', 'out', 'path', 'plot', 'skip'}
ROUTE = ('create', 'xdmf')
PRIORITY = {'ignore'}
CRATES = (adapt_arguments, log_messages, attach_context)
DROPS = {'auto', 'find', 'force', 'high', 'ignore', 'low', 'skip'}
MAPPING = {'grid': 'gridname', 'out': 'filename', 'plot': 'plotname', 'path': 'source'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

@safe
def xdmf(**arguments: Any) -> None:
    """Python application interface for creating xdmf from command line or python code.
    
    This method creates a metadata file (i.e., xdmf format) associated with a desired set of HDF5 binary
    simulation data suitable for using in supporting visualization software (e.g., Paraview). The arguments
    povide flexibility in creating this metadata file that covers most usecases (e.g., time-series 3d data).

    Keyword Arguments:
        basename (str): Basename for flash simulation, will be guessed if not provided
                        (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)
        low (int):      Begining number for timeseries hdf5 files.
        high (int):     Ending number for timeseries hdf5 files.
        skip (int):     Number of files to skip for timeseries hdf5 files.
        files (list):   List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
        path (str):     Path to timeseries hdf5 simulation output files.
        dest (str):     Path to xdmf (contains relative paths to sim data).
        out (str):      Output XDMF file name follower.
        plot (str):     Plot/Checkpoint file(s) name follower.
        grid (str):     Grid file(s) name follower.
        force (str):    Plot/Checkpoint file(s) substring to ignore.
        auto (bool):    Force behavior to attempt guessing BASENAME and [--files LIST].
        find (bool):    Force behavior to attempt guessing [--files LIST].
        ignore (bool):  Ignore configuration file provided arguments, options, and flags.

    Note:
        If neither BASENAME nor either of [LOW/HIGH/SKIP] or -f is specified,
        the PATH will be searched for flash simulation files and all
        such files identified will be used in sorted order."""
    create_xdmf(**process_arguments(**arguments))
