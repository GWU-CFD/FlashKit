"""Create an initial flow field (block) using interpolated simulation data."""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
from ...api.create import interp
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_options
from ...core.parse import DictStr, DictListStr

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface 

logger = logging.getLogger(__name__)

DEF = get_defaults().create.interp

PROGRAM = f'flashkit create interp'

USAGE = f"""\
usage: {PROGRAM} BASENAME [<option> VALUE, ...] [<switch>, ...] [<flag>, ...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:  
BASENAME    Basename for flash simulation, will be guessed if not provided
            (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)

options:
-D, --ndim     INT   Number of simulation dimensions (i.e., 2 or 3); defaults to {DEF.ndim}.
-X, --nxb      INT   Number of grid points per block in the i direction; defaults to {DEF.nxb}.
-Y, --nyb      INT   Number of grid points per block in the j direction; defaults to {DEF.nyb}.
-Z, --nzb      INT   Number of grid points per block in the k direction; defaults to {DEF.nzb}.
-i, --iprocs   INT   Number of blocks in the i direction; defaults to {DEF.iprocs}.
-j, --jprocs   INT   Number of blocks in the j direction; defaults to {DEF.jprocs}.
-k, --kprocs   INT   Number of blocks in the k direction; defaults to {DEF.kprocs}.
-l, --fields   DICT  Key/value pairs for final fields (e.g., <velx=facex,...>); defaults are
                         {dict(DEF.fields)}.
-m, --fsource  DICT  Key/value pairs for source fields (e.g., <velx=(cc_u,center),...>); defaults to FIELDS.
-f, --step     INT   File number (e.g., <1,3,5,7,9>) of source timeseries output.
-g, --grid   STRING  Grid file(s) name follower; defaults to '{DEF.grid}'.
-c, --plot   STRING  Plot/Checkpoint file(s) name follower; defaults to '{DEF.plot}'.
-q, --force  STRING  Plot/Checkpoint file(s) substring to ignore; defaults to '{DEF.force}'.
-p, --path     PATH  Path to source files used in some initialization methods (e.g., python); defaults to cwd.
-d, --dest     PATH  Path to intial block hdf5 file; defaults to cwd.

switches:
-A, --auto           Force behavior to attempt guessing BASENAME and [--step INT].
-B, --find           Force behavior to attempt guessing [--step INT].

flags:
-F, --nofile         Do not write the calculated coordinates to file. 
-R, --result         Return the calculated fields by block on root. 
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
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
    interface.add_argument('-q', '--force')
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')

    auto_interface = interface.add_mutually_exclusive_group()
    auto_interface.add_argument('-A', '--auto', action='store_const', const=True)
    auto_interface.add_argument('--no_auto', dest='auto', action='store_const', const=False)

    find_interface = interface.add_mutually_exclusive_group()
    find_interface.add_argument('-B', '--find', action='store_const', const=True)
    find_interface.add_argument('--no-find', dest='find', action='store_const', const=False)

    interface.add_argument('-F', '--nofile', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')

    interface.add_argument('--correct', action='store_true') ## FUTURE

    def run(self) -> None:
        """Buisness logic for creating block using interpolatione, from command line."""
        
        if getattr(self, 'options'): 
            return_options(['create', 'interp'])
            return

        options ={'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields', 'fsource', 'step', 
                  'plot', 'grid', 'force', 'path', 'dest', 'auto', 'find', 'ignore', 'result', 'nofile'}
        if self.shared.future: ## FUTURE
            options.add('correct')
        elif self.correct:
            logger.warn('Attempting to use option --correct without invoking --future.')
        local = {key: getattr(self, key) for key in options}
        logger.debug('Command -- Entry point for interp command.')
        interp(**local, cmdline=True)
