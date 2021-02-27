"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import List, Optional

# standard libraries
import os
import sys
import re
from functools import partial

# internal libraries
from ...api.create import grid
from ...api.create.grid import NDIM, NXB, NYB, NZB, XRANGE, YRANGE, ZRANGE, XMETHOD, YMETHOD, ZMETHOD
from ...core.error import AutoError, StreamError

# external libraries
from cmdkit.app import Application, exit_status
from cmdkit.cli import Interface, ArgumentError 

PROGRAM = f'flashkit create grid'

USAGE = f"""\
usage: {PROGRAM} [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

options:
-D, --ndim     INT   Number of simulation dimensions (i.e., 2 or 3); defaults to {NDIM}.
-X, --nxb      INT   Number of grid points per block in the i direction; defaults to {NXB}.
-Y, --nyb      INT   Number of grid points per block in the j direction; defaults to {NYB}.
-Z, --nzb      INT   Number of grid points per block in the k direction; defaults to {NZB}.
-x, --xrange   LIST  Bounding points (e.g., <0.0,1.0>) for i direction; defaults to {XRANGE}.
-y, --yrange   LIST  Bounding points (e.g., <0.0,1.0>) for j direction; defaults to {YRANGE}.
-z, --zrange   LIST  Bounding points (e.g., <0.0,1.0>) for k direction; defaults to {ZRANGE}.
-B, --bndbox   LIST  Bounding box pairs (e.g., <0.0,1.0,...>) for each of i,j,k directions.
-a, --xmethod  STR   Stretching method for grid points in the i directions; defaults to {XMETHOD}.
-b, --ymethod  STR   Stretching method for grid points in the j directions; defaults to {YMETHOD}.
-c, --zmethod  STR   Stretching method for grid points in the k directions; defaults to {ZMETHOD}.
-q, --xparam   DICT  Key/value pairs for paramaters (e.g., <alpha=0.5,...>) used for i direction method.
-r, --yparam   DICT  Key/value pairs for paramaters (e.g., <alpha=0.5,...>) used for j direction method.
-s, --zparam   DICT  Key/value pairs for paramaters (e.g., <alpha=0.5,...>) used for k direction method.
-p, --path     PATH  Path to source files used in some streching methods (e.g., ascii); defaults to cwd.
-d, --dest     PATH  Path to intial grid hdf5 file; defaults to cwd.

flags:
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-h, --help           Show this message and exit.\
"""

# default constants
STR_FAILED = 'Unable to create grid file!'

# Create argpase List custom types
ListIntType = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 
ListFloatType = lambda l: [float(i) for i in re.split(r',\s|,|\s', l)] 
DictStrType = lambda d: dict((k.strip(), v.strip()) for k, v in (re.split(r'=\s|=', i) for i in re.split(r',\s|,', d)))

def log_exception(exception: Exception, status: int = exit_status.runtime_error) -> int:
    """Custom exception handler for this module."""
    message, *_ = exception.args
    Application.log_critical('\n'.join([STR_FAILED, message]))
    return status

def error(message: str) -> None:
    """Override simple raise w/ formatted message."""
    raise ArgumentError('\n'.join((STR_FAILED, message)))

class GridCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', error)

    ALLOW_NOARGS: bool = True

    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int) 
    interface.add_argument('-x', '--xrange', type=ListFloatType)
    interface.add_argument('-y', '--yrange', type=ListFloatType)
    interface.add_argument('-z', '--zrange', type=ListFloatType)
    interface.add_argument('-B', '--bndbox', type=ListFloatType)
    interface.add_argument('-a', '--xmethod')
    interface.add_argument('-b', '--ymethod')
    interface.add_argument('-c', '--zmethod')
    interface.add_argument('-q', '--xparam', type=DictStrType)
    interface.add_argument('-r', '--yparam', type=DictStrType)
    interface.add_argument('-s', '--zparam', type=DictStrType)
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-I', '--ignore', action='store_true')

    exceptions = {error: partial(log_exception, status=exit_status.runtime_error) 
        for error in {AutoError, StreamError, OSError}}

    def run(self) -> None:
        """Buisness logic for creating grid from command line."""
        options ={'ndim', 'nxb', 'nyb', 'nzb', 'xrange', 'yrange', 'zrange', 'bndbox',
                  'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam',
                  'path', 'dest', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        grid(**local)
