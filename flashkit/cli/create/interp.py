"""Create an initial flow field (block) using interpolated simulation data."""

# type annotations
from __future__ import annotations

# internal libraries
from ...api.create import interp
from ...api.create.interp import NDIM, NXB, NYB, NZB, IPROCS, JPROCS, KPROCS, FIELDS, PLOT, GRID
from ...core.custom import patched_error, patched_exceptions
from ...core.parse import DictStr, DictListStr

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface 

PROGRAM = f'flashkit create interp'

USAGE = f"""\
usage: {PROGRAM} BASENAME [--step INT] [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:  
BASENAME    Basename for flash simulation, will be guessed if not provided
            (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)

options:
-D, --ndim     INT   Number of simulation dimensions (i.e., 2 or 3); defaults to {NDIM}.
-X, --nxb      INT   Number of grid points per block in the i direction; defaults to {NXB}.
-Y, --nyb      INT   Number of grid points per block in the j direction; defaults to {NYB}.
-Z, --nzb      INT   Number of grid points per block in the k direction; defaults to {NZB}.
-i, --iprocs   INT   Number of blocks in the i direction; defaults to {IPROCS}.
-j, --jprocs   INT   Number of blocks in the j direction; defaults to {JPROCS}.
-k, --kprocs   INT   Number of blocks in the k direction; defaults to {KPROCS}.
-l, --fields   DICT  Key/value pairs for final fields (e.g., <velx=facex,...>); defaults are
                         {FIELDS}.
-m, --fsource  DICT  Key/value pairs for source fields (e.g., <velx=(cc_u,center),...>); defaults to FIELDS.
-f, --step     INT   File number (e.g., <1,3,5,7,9>) of source timeseries output.
-g, --grid   STRING  Grid file(s) name follower; defaults to '{GRID}'.
-o, --plot   STRING  Plot/Checkpoint file(s) name follower; defaults to '{PLOT}'.
-p, --path     PATH  Path to source files used in some initialization methods (e.g., python); defaults to cwd.
-d, --dest     PATH  Path to intial block hdf5 file; defaults to cwd.

flags:
-A, --auto           Force behavior to attempt guessing BASENAME and [--step INT].
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-R, --result         Return the calculated fields by block on root. 
-F, --nofile         Do not write the calculated coordinates to file. 
-h, --help           Show this message and exit.

notes:  If neither BASENAME nor -f is specified, the --path will be searched for FLASH simulation
        files and the last such file (in sorted order) identified will be used.\

        This function reads grid data from an hdf5 file (i.e., must run <flashkit create grid> first).\
"""

# default constants
STR_FAILED = 'Unable to create block file!'

class InterpCreateApp(Application):
    """Application class for create interp command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True

    interface.add_argument('basename', nargs='?')
    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int) 
    interface.add_argument('-i', '--iprocs', type=int) 
    interface.add_argument('-j', '--jprocs', type=int) 
    interface.add_argument('-k', '--kprocs', type=int) 
    interface.add_argument('-l', '--fields', type=DictStr)
    interface.add_argument('-m', '--fsource', type=DictListStr)
    interface.add_argument('-f', '--step', type=int)
    interface.add_argument('-g', '--grid')
    interface.add_argument('-o', '--plot')
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-A', '--auto', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-F', '--nofile', action='store_true')

    def run(self) -> None:
        """Buisness logic for creating block using interpolatione, from command line."""
        options ={'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields', 'fsource', 'step', 
                  'plot', 'grid', 'path', 'dest', 'auto', 'ignore', 'result', 'nofile'}
        local = {key: getattr(self, key) for key in options}
        interp(**local, cmdline=True)
