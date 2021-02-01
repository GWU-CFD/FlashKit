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
from ...library import create_xdmf
from ...resources import CONFIG, DEFAULTS
from ..core import get_arguments, get_defaults

# external libraries
from cmdkit.app import Application, exit_status
from cmdkit.cli import Interface, ArgumentError 
from alive_progress import alive_bar, config_handler

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
-b, --low    INT     Begining number for timeseries hdf5 files; defaults to {create_xdmf.LOW}.
-e, --high   INT     Ending number for timeseries hdf5 files; defaults to {create_xdmf.HIGH}.
-s, --skip   INT     Number of files to skip for timeseries hdf5 files; defaults to {create_xdmf.SKIP}.
-f, --files  LIST    List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
-p, --path   PATH    Path to timeseries hdf5 simulation output files; defaults to cwd.
-o, --out    FILE    Output XDMF file name follower; defaults to no footer.
-i, --plot   STRING  Plot/Checkpoint file(s) name follower; defaults to '{create_xdmf.PLOT}'.
-g, --grid   STRING  Grid file(s) name follower; defaults to '{create_xdmf.GRID}'.

flags:
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-A, --auto           Force behavior to attempt guessing BASENAME and [--files LIST].
-h, --help           Show this message and exit.

notes:  If neither BASENAME nor either of [-b/-e/-s] or -f is specified,
        the --path will be searched for FLASH simulation files and all
        such files identified will be used in sorted order.\
"""

# default constants
STR_INCLUDE = re.compile(DEFAULTS['general']['files']['plot'])
STR_EXCLUDE = re.compile(DEFAULTS['general']['files']['forced'])
STR_FAILED = 'Unable to create xdmf file!'
BAR_SWITCH = CONFIG['create']['xdmf']['switch']

# Create argpase List custom types
IntListType = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 

def log_exception(exception: Exception, status: int = exit_status.runtime_error) -> int:
    """Custom exception handler for this module."""
    message, *_ = exception.args
    Application.log_critical('\n'.join([STR_FAILED, message]))
    return status

def error(message: str) -> None:
    """Override simple raise w/ formatted message."""
    print(f'\n{STR_FAILED}')
    raise ArgumentError(message)

class AutoError(Exception):
    """Raised when cannot automatically determine files."""

class XdmfCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    interface.error = error

    ALLOW_NOARGS: bool = True

    basename: Optional[str] = None
    interface.add_argument('basename', nargs='?', default=basename)

    low: Optional[int] = None 
    interface.add_argument('-b', '--low', type=int) 

    high: Optional[int] = None 
    interface.add_argument('-e', '--high', type=int) 

    skip: Optional[int] = None
    interface.add_argument('-s', '--skip', type=int) 

    files: Optional[List[int]] = None
    interface.add_argument('-f', '--files', type=IntListType)

    path: Optional[str] = None
    interface.add_argument('-p', '--path')

    output: Optional[str] = None
    interface.add_argument('-o', '--out')

    plot: Optional[str] = None
    interface.add_argument('-i', '--plot')

    grid: Optional[str] = None
    interface.add_argument('-g', '--grid')

    ignore: Optional[bool] = None
    interface.add_argument('-I', '--ignore', action='store_true')

    auto: Optional[bool] = None
    interface.add_argument('-A', '--auto', action='store_true')

    exceptions = {AutoError: partial(log_exception, status=exit_status.runtime_error),
                  OSError: partial(log_exception, status=exit_status.runtime_error)}

    def run(self) -> None:
        """Buisness logic for creating xdmf from command line."""

        # determine if arguments passed (assumed values if parsing config files)
        if self.ignore:
            range_given = any({self.low, self.high, self.skip})
            files_given = self.files is not None
            bname_given = self.basename is not None
        else:
            range_given = True
            files_given = False
            bname_given = False

        # force automatic if desired
        if self.auto:
            range_given = False
            file_given = False
            bname_given = False
        
        # optionally use configuration files
        options = {'basename', 'low', 'high', 'skip', 'files', 'path', 'out', 'plot', 'grid'}
        local = {key: getattr(self, key) for key in options}
        local = {'create': {'xdmf': {key: value for key, value in local.items() if value is not None}}} 
        if self.ignore:
            arguments = get_defaults(local=local)['create']['xdmf']
        else:
            arguments = get_arguments(local=local)['create']['xdmf']
        for key, value in arguments.items():
            setattr(self, key, value)

        # prepare conditions in order to arrang a list of files to process
        if (not files_given and not range_given) or not bname_given:
            files = os.listdir(os.getcwd() + '/' + self.path + '')
            condition = lambda file: re.search(STR_INCLUDE, file) and not re.search(STR_EXCLUDE, file)

        # create the filelist
        if not files_given: 
            if range_given:
                if self.low is None:
                    self.low = create_xdmf.LOW
                if self.high is None:
                    self.high = create_xdmf.HIGH
                if self.skip is None:
                    self.skip = create_xdmf.SKIP
                self.high = self.high + 1
                self.files = range(self.low, self.high, self.skip)
            else:
                self.files = sorted([int(file[-4:]) for file in files if condition(file)])
                if not self.files:
                    raise AutoError(f'Cannot automatically identify simulation files on path {self.path}')
        else:
            pass

        # create the basename
        if not bname_given:
            try:
                self.basename, *_ = next(filter(condition, (file for file in files))).split(STR_INCLUDE.pattern)
            except StopIteration:
                raise AutoError(f'Cannot automatically parse basename for simulation files on path {self.path}')
        else:
            pass

        # Prepare useful messages
        message = '\n'.join([
            f'Creating xdmf file from {len(self.files)} simulation files',
            f'  plotfiles = {self.path}{self.basename}{self.plot}xxxx',
            f'  gridfiles = {self.path}{self.basename}{self.grid}xxxx',
            f'  xdmf_file = {self.path}{self.basename}{self.out}.xmf',
            f'',
            ])

        # Create xdmf file using core library; optionally w/ progress bar
        if len(self.files) >= BAR_SWITCH and sys.stdout.isatty():
            config_handler.set_global(theme='smooth', unknown='horizontal')
            print(message)
            create_xdmf.file(files=self.files, basename=self.basename, path=self.path, filename=self.out, 
                             plotname=self.plot, gridname=self.grid, context=alive_bar)
        else:
            message += '\nWriting xdmf data out to file ...'
            print(message)
            create_xdmf.file(files=self.files, basename=self.basename, path=self.path, filename=self.out, 
                             plotname=self.plot, gridname=self.grid)
