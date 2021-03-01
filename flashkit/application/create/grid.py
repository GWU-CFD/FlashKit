"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations

# internal libraries
from ...api.create import grid
from ...api.create.grid import (NDIM, NXB, NYB, NZB, IPROCS, JPROCS, KPROCS, 
        XRANGE, YRANGE, ZRANGE, XMETHOD, YMETHOD, ZMETHOD)
from ...core.custom import patched_error, patched_exceptions, ListFloat, DictStr

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface 

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
-i, --iprocs   INT   Number of blocks in the i direction; defaults to {IPROCS}.
-j, --jprocs   INT   Number of blocks in the j direction; defaults to {JPROCS}.
-k, --kprocs   INT   Number of blocks in the k direction; defaults to {KPROCS}.
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
-R, --result         Return the calculated coordinates. 
-F, --nofile         Do not write the calculated coordinates to file. 
-h, --help           Show this message and exit.\
"""

# default constants
STR_FAILED = 'Unable to create grid file!'

class GridCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True

    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int) 
    interface.add_argument('-i', '--iprocs', type=int) 
    interface.add_argument('-j', '--jprocs', type=int) 
    interface.add_argument('-k', '--kprocs', type=int) 
    interface.add_argument('-x', '--xrange', type=ListFloat)
    interface.add_argument('-y', '--yrange', type=ListFloat)
    interface.add_argument('-z', '--zrange', type=ListFloat)
    interface.add_argument('-B', '--bndbox', type=ListFloat)
    interface.add_argument('-a', '--xmethod')
    interface.add_argument('-b', '--ymethod')
    interface.add_argument('-c', '--zmethod')
    interface.add_argument('-q', '--xparam', type=DictStr)
    interface.add_argument('-r', '--yparam', type=DictStr)
    interface.add_argument('-s', '--zparam', type=DictStr)
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-F', '--nofile', action='store_true')

    def run(self) -> None:
        """Buisness logic for creating grid from command line."""
        options ={'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'xrange', 'yrange', 'zrange', 'bndbox', 
                  'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam', 'path', 'dest', 
                  'ignore', 'result', 'nofile'}
        local = {key: getattr(self, key) for key in options}
        grid(**local, cmdline=True)
