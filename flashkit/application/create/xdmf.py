"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import List, Optional

# standard libraries
import os
import sys
import re
from functools import partial

# internal libraries
from ...api.create import xdmf
from ...api.create.xdmf import LOW, HIGH, SKIP, PLOT, GRID, OUT
from ...core.error import AutoError, StreamError

# external libraries
from cmdkit.app import Application, exit_status
from cmdkit.cli import Interface, ArgumentError 

PROGRAM = f'flashkit create xdmf'

USAGE = f"""\
usage: {PROGRAM} BASENAME [--low INT] [--high INT] [--skip INT] [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:  
BASENAME    Basename for flash simulation, will be guessed if not provided
            (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)

options:
-b, --low    INT     Begining number for timeseries hdf5 files; defaults to {LOW}.
-e, --high   INT     Ending number for timeseries hdf5 files; defaults to {HIGH}.
-s, --skip   INT     Number of files to skip for timeseries hdf5 files; defaults to {SKIP}.
-f, --files  LIST    List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
-p, --path   PATH    Path to timeseries hdf5 simulation output files; defaults to cwd.
-d, --dest   PATH    Path to xdmf (contains relative paths to sim data); defaults to cwd.
-o, --out    FILE    Output XDMF file name follower; defaults to a footer '{OUT}'.
-i, --plot   STRING  Plot/Checkpoint file(s) name follower; defaults to '{PLOT}'.
-g, --grid   STRING  Grid file(s) name follower; defaults to '{GRID}'.

flags:
-A, --auto           Force behavior to attempt guessing BASENAME and [--files LIST].
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-h, --help           Show this message and exit.

notes:  If neither BASENAME nor either of [-b/-e/-s] or -f is specified,
        the --path will be searched for FLASH simulation files and all
        such files identified will be used in sorted order.\
"""

# default constants
STR_FAILED = 'Unable to create xdmf file!'

# Create argpase List custom types
IntListType = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 

def log_exception(exception: Exception, status: int = exit_status.runtime_error) -> int:
    """Custom exception handler for this module."""
    message, *_ = exception.args
    Application.log_critical('\n'.join([STR_FAILED, message]))
    return status

def error(message: str) -> None:
    """Override simple raise w/ formatted message."""
    raise ArgumentError('\n'.join((STR_FAILED, message)))

class XdmfCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', error)

    ALLOW_NOARGS: bool = True

    interface.add_argument('basename', nargs='?')
    interface.add_argument('-b', '--low', type=int) 
    interface.add_argument('-e', '--high', type=int) 
    interface.add_argument('-s', '--skip', type=int) 
    interface.add_argument('-f', '--files', type=IntListType)
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-o', '--out')
    interface.add_argument('-i', '--plot')
    interface.add_argument('-g', '--grid')
    interface.add_argument('-A', '--auto', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')

    exceptions = {error: partial(log_exception, status=exit_status.runtime_error) 
        for error in {AutoError, StreamError, OSError}}

    def run(self) -> None:
        """Buisness logic for creating xdmf from command line."""
        options = {'basename', 'low', 'high', 'skip', 'files', 'path', 'dest', 
                   'out', 'plot', 'grid', 'auto', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        xdmf(**local)
