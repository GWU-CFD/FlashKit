"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
from ...api.create import grid
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_options
from ...core.parse import ListFloat, DictAny

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface 

logger = logging.getLogger(__name__)

DEF = get_defaults().create.grid

PROGRAM = f'flashkit create grid'

USAGE = f"""\
usage: {PROGRAM} [<option> VALUE, ...] [<flag>, ...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

options:
-D, --ndim     INT   Number of simulation dimensions (i.e., 2 or 3); defaults to {DEF.ndim}.
-X, --nxb      INT   Number of grid points per block in the i direction; defaults to {DEF.nxb}.
-Y, --nyb      INT   Number of grid points per block in the j direction; defaults to {DEF.nyb}.
-Z, --nzb      INT   Number of grid points per block in the k direction; defaults to {DEF.nzb}.
-i, --iprocs   INT   Number of blocks in the i direction; defaults to {DEF.iprocs}.
-j, --jprocs   INT   Number of blocks in the j direction; defaults to {DEF.jprocs}.
-k, --kprocs   INT   Number of blocks in the k direction; defaults to {DEF.kprocs}.
-x, --xrange   LIST  Bounding points (e.g., <0.0,1.0>) for i direction; defaults to {DEF.xrange}.
-y, --yrange   LIST  Bounding points (e.g., <0.0,1.0>) for j direction; defaults to {DEF.yrange}.
-z, --zrange   LIST  Bounding points (e.g., <0.0,1.0>) for k direction; defaults to {DEF.zrange}.
-B, --bndbox   LIST  Bounding box pairs (e.g., <0.0,1.0,...>) for each of i,j,k directions.
-a, --xmethod  STR   Stretching method for grid points in the i directions; defaults to {DEF.xmethod}.
-b, --ymethod  STR   Stretching method for grid points in the j directions; defaults to {DEF.ymethod}.
-c, --zmethod  STR   Stretching method for grid points in the k directions; defaults to {DEF.zmethod}.
-q, --xparam   DICT  Key/value pairs for paramaters (e.g., <alpha=0.5,...>) used for i direction method.
-r, --yparam   DICT  Key/value pairs for paramaters (e.g., <alpha=0.5,...>) used for j direction method.
-s, --zparam   DICT  Key/value pairs for paramaters (e.g., <alpha=0.5,...>) used for k direction method.
-p, --path     PATH  Path to source files used in some streching methods (e.g., ascii); defaults to cwd.
-d, --dest     PATH  Path to intial grid hdf5 file; defaults to cwd.

flags:
-F, --nofile         Do not write the calculated coordinates to file. 
-R, --result         Return the calculated coordinates. 
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-h, --help           Show this message and exit.\
"""

# default constants
STR_FAILED = 'Unable to create grid file!'

class GridCreateApp(Application):
    """Application class for create grid command."""

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
    interface.add_argument('-q', '--xparam', type=DictAny)
    interface.add_argument('-r', '--yparam', type=DictAny)
    interface.add_argument('-s', '--zparam', type=DictAny)
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-F', '--nofile', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')

    def run(self) -> None:
        """Buisness logic for creating grid from command line."""
        
        if getattr(self, 'options'): 
            return_options(['create', 'grid'])
            return

        options ={'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'xrange', 'yrange', 'zrange', 'bndbox', 
                  'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam', 'path', 'dest', 
                  'ignore', 'result', 'nofile'}
        local = {key: getattr(self, key) for key in options}
        logger.debug('Command -- Entry point for grid command.')
        grid(**local, cmdline=True)
