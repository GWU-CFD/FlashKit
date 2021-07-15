"""Build and compile a FLASH simulation directory."""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
from ...api.build import simulation
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_available, return_options
from ...core.parse import DictAny, ListStr

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().build.simulation

PROGRAM = f'flashkit build simulation'

USAGE = f"""\
usage: {PROGRAM} SIMULATION DIRECTORY [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:  
SIMULATION  STRING  Specify a simulation directory contained in the FLASH source/Simulation/SimulationMain.
DIRECTORY   STRING  Specify a build directory basename; will be determined if not provided. 

options:
-D, --ndim       INT     Number of simulation dimensions (i.e., 2 or 3); defaults to {DEF.ndim}.
-X, --nxb        INT     Number of grid points per block in the i direction; defaults to {DEF.nxb}.
-Y, --nyb        INT     Number of grid points per block in the j direction; defaults to {DEF.nyb}.
-Z, --nzb        INT     Number of grid points per block in the k direction; defaults to {DEF.nzb}.
-g, --grid       STRING  Type of FLASH simulation grid used by the Grid Package; defaults to {DEF.grid}.
-m, --python     INT     Python version for the setup script; specifically use either 2 (legacy) or 3 (modern); defaults to {DEF.python}.
-c, --site       STRING  Hostname of the machine on which setup is being run; Makefile should be in sites/SITE; defaults to {DEF.site}.
-o, --optimize   STRING  Flag for compilation and linking; using either optimized, debugging, or other; defaults to {DEF.optimize}. 
-q, --shortcuts  LIST    Additional setup shortcuts (example: +rg) which begin with a plus symbol.  
-f, --flags      LIST    Additional setup options (example: -auto) which begin with a dash.
-s, --variables  DICT    Additional setup variable pairs (example: -nxb=12) which begin with a dash.
-u, --subpath    STRING  Path to SIMULATION within source/Simulation/SimulationMain; defaults to {DEF.subpath}.
-p, --path       STRING  Path to the local FLASH source repository; defaults to {DEF.path}.
-j, --jobs       INT     Number of parallel processes to use when executing the make command; defaults to {DEF.jobs}.

flags:
-H, --parallelIO  Use the parallel HDF5 Input/Output library.
-C, --compile     Compile the FLASH simulation build directory after it is constructed.
-B, --build       Force the building of the simulation directory, even if the directory exists. 
-F, --force       Force the compilation of the build directory, even if the binary is present. 
-I, --ignore      Ignore configuration file provided arguments, options, and flags.
-O, --options     Show the available options (i.e., defaults and config file format) and exit.
-h, --help        Show this message and exit.
"""

# default constants
STR_FAILED = 'Unable to build simulation directory!'

class SimulationBuildApp(Application):
    """Application class for build simulation command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)

    ALLOW_NOARGS: bool = True

    interface.add_argument('simulation', nargs='?')
    interface.add_argument('directory', nargs='?')
    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int)
    interface.add_argument('-g', '--grid')
    interface.add_argument('-m', '--python', type=int)
    interface.add_argument('-c', '--site')
    interface.add_argument('-o', '--optimize')
    interface.add_argument('-q', '--shortcuts', type=ListStr)
    interface.add_argument('-f', '--flags', type=ListStr)
    interface.add_argument('-s', '--variables', type=DictAny)
    interface.add_argument('-p', '--path')
    interface.add_argument('-j', '--jobs', type=int)
    interface.add_argument('-H', '--parallelIO', action='store_true')
    interface.add_argument('-C', '--compile', action='store_true')
    interface.add_argument('-B', '--build', action='store_true')
    interface.add_argument('-F', '--force', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')

    def run(self) -> None:
        """Buisness logic for building simulation directories from command line."""
        
        if getattr(self, 'options'): 
            return_options(['build', 'simulation'])
            return

        options = {'simulation', 'directory', 'ndim', 'nxb', 'nyb', 'nzb', 'grid', 'python',
                   'site', 'optimize', 'shortcuts', 'flags', 'variables', 'path', 'jobs',
                   'parallelIO', 'compile', 'build', 'force', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        simulation(**local, cmdline=True)
