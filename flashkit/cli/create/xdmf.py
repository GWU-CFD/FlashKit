"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import List, Optional

# standard libraries
import os
import re
from functools import partial

# internal libraries
from ...lib import create_xdmf

# external libraries
from cmdkit.app import Application, exit_status
from cmdkit.cli import Interface, ArgumentError 
from alive_progress import alive_bar, config_handler

PROGRAM = f'flash create xdmf'

USAGE = f"""\
usage: {PROGRAM} BASENAME [[<opt> <arg(s)>]...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
BASENAME            Basename for flash simulation, will be guessed if not provided
                    (e.g., INS_Rayleigh for files INS_Rayleigh_hdf5_plt_cnt_xxxx)

note:               If neither BASENAME nor either of [-b/-e/-s] or -f is specified,
                    the --path will be searched for FLASH simulation files and all
                    such files identified will be used in sorted order.

options:
-b, --low           Begining number for timeseries hdf5 files; defaults to {create_xdmf.LOW}.
-e, --high          Ending number for timeseries hdf5 files; defaults to {create_xdmf.HIGH}.
-s, --skip          Number of files to skip for timeseries hdf5 files; defaults to {create_xdmf.SKIP}.
-f, --files         List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
-p, --path          Path to timeseries hdf5 simulation output files; defaults to cwd.
-o, --out           Output XDMF file name follower; defaults to no footer.
-i, --plot          Plot/Checkpoint file(s) name follower; defaults to '{create_xdmf.PLOT}'.
-g, --grid          Grid file(s) name follower; defaults to '{create_xdmf.GRID}'.
-h, --help          Show this message and exit.\
"""

# default constants
STR_INCLUDE = re.compile('_hdf5_plt_cnt_')
STR_EXCLUDE = re.compile('forced')
STR_FAILED = 'Unable to create xdmf file!'
BAR_SWITCH = 20

# Create argpase List custom types
IntListType = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 

# Custom exception handler for this module
def log_exception(exception: Exception, status: int = exit_status.runtime_error) -> int:
    message, *_ = exception.args
    Application.log_critical(f'\n{STR_FAILED}\n{message}')
    return status

# Override simple raise w/ formatted message
def error(message: str) -> None:
    print(f'\n{STR_FAILED}')
    raise ArgumentError(message)

class AutoError(Exception):
    """Raised when cannot automatically determine files"""

class XdmfCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    interface.error = error

    ALLOW_NOARGS: bool = True

    basename: Optional[str] = None
    interface.add_argument('basename', nargs='?', default=basename)

    low: Optional[int] = None 
    interface.add_argument('-b', '--low', type=int, default=low) 

    high: Optional[int] = None 
    interface.add_argument('-e', '--high', type=int, default=high) 

    skip: Optional[int] = None
    interface.add_argument('-s', '--skip', type=int, default=skip) 

    files: Optional[List[int]] = None
    interface.add_argument('-f', '--files', type=IntListType, default=files)

    path: str = create_xdmf.PATH
    interface.add_argument('-p', '--path', default=path)

    output: str = create_xdmf.OUTPUT
    interface.add_argument('-o', '--out', default=output)

    plot: str = create_xdmf.PLOT
    interface.add_argument('-i', '--plot', default=plot)

    grid: str = create_xdmf.GRID
    interface.add_argument('-g', '--grid', default=grid)

    exceptions = {AutoError: partial(log_exception, status=exit_status.runtime_error)} 

    def run(self) -> None:
        """Buisness logic for creating xdmf from command line."""

        # prepare conditions in order to arrang a list of files to process
        range_given = any({self.low, self.high, self.skip})
        if (self.files is None and not range_given) or self.basename is None:
            files = os.listdir(os.getcwd() + '/' + '')
            condition = lambda file: re.search(STR_INCLUDE, file) and not re.search(STR_EXCLUDE, file)

        # create the filelist
        if self.files is None: 
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
                    raise AutoError(f'cannot automatically identify simulation files on path {self.path}')
        else:
            pass

        # create the basename
        if self.basename is None:
            try:
                self.basename = next(filter(condition, (file for file in files))).split(STR_INCLUDE.pattern)[0]
            except StopIteration:
                raise AutoError(f'cannot automatically parse basename for simulation files on path {self.path}')
        else:
            pass

        # Create xdmf file using core library, w/ useful messages and progress bar
        arguments = {'files': self.files, 'basename': self.basename, 'path': self.path, 
                     'filename': self.output, 'plotname': self.plot, 'gridname': self.grid}
        message = f'Creating xdmf file from {len(self.files)} simulation files\n'
        message += f'  plotfiles = {self.path}{self.basename}{self.plot}xxxx\n'
        message += f'  gridfiles = {self.path}{self.basename}{self.grid}xxxx\n'
        message += f'  xdmf_file = {self.path}{self.basename}{self.output}.xmf\n'
        if len(self.files) >= BAR_SWITCH:
            arguments['context'] = alive_bar
            config_handler.set_global(theme='smooth', unknown='horizontal')
        else:
            message = message + '\nWriting xdmf data out to file ...'
        print(message)
        create_xdmf.file(**arguments)
