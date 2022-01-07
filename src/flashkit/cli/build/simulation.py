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
usage: {PROGRAM} PATH NAME [<option> VALUE, ...] [<switch>, ...] [<flag>, ...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:  
PATH        STRING  Specify a simulation directory contained in the FLASH source/Simulation/SimulationMain.
NAME        STRING  Specify a build directory basename; will not be determined if not provided. 

options:
-D, --ndim       INT     Number of simulation dimensions (i.e., 2 or 3); defaults to {DEF.ndim}.
-X, --nxb        INT     Number of grid points per block in the i direction; defaults to {DEF.nxb}.
-Y, --nyb        INT     Number of grid points per block in the j direction; defaults to {DEF.nyb}.
-Z, --nzb        INT     Number of grid points per block in the k direction; defaults to {DEF.nzb}.
-g, --grid       STRING  Type of FLASH simulation grid used by the Grid Package; defaults to {DEF.grid}.
-p, --python     INT     Python version for the setup script; specifically use either 2 (legacy) or 3 (modern); defaults to {DEF.python}.
-s, --site       STRING  Hostname of the machine on which setup is being run; Makefile should be in sites/SITE; defaults to {DEF.site}.
-o, --optimize   STRING  Flag for compilation and linking; using either optimized, debugging, or other; defaults to {DEF.optimize}. 
-l, --shortcuts  LIST    Additional setup shortcuts (example: +rg) which begin with a plus symbol.  
-m, --flags      LIST    Additional setup options (example: -auto) which begin with a dash.
-n, --variables  DICT    Additional setup variable pairs (example: -nxb=12) which begin with a dash.
-u, --subspath   STRING  Path to SIMULATION within source/Simulation/SimulationMain; defaults to {DEF.subpath}.
-b, --source     STRING  Path to the local FLASH source repository; defaults to {DEF.source}.
-j, --jobs       INT     Number of parallel processes to use when executing the make command; defaults to {DEF.jobs}.

switches:
-H, --parallelIO  Use the parallel HDF5 Input/Output library.
-C, --compile     Compile the FLASH simulation build directory after it is constructed.
-B, --build       Force the building of the simulation directory, even if the directory exists. 
-F, --force       Force the compilation of the build directory, even if the binary is present. 

flags:
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

    interface.add_argument('path', nargs='?')
    interface.add_argument('name', nargs='?')
    
    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int)
    interface.add_argument('-g', '--grid')
    interface.add_argument('-p', '--python', type=int)
    interface.add_argument('-s', '--site')
    interface.add_argument('-o', '--optimize')
    interface.add_argument('-l', '--shortcuts', type=ListStr)
    interface.add_argument('-m', '--flags', type=ListStr)
    interface.add_argument('-n', '--variables', type=DictAny)
    interface.add_argument('-u', '--subpath')
    interface.add_argument('-b', '--source')
    interface.add_argument('-j', '--jobs', type=int)

    parallelIO_interface = interface.add_mutually_exclusive_group()
    parallelIO_interface.add_argument('-H', '--parallelIO', action='store_true')
    parallelIO_interface.add_argument('--no-parallelIO', dest='parallelIO', action='store_false')

    compile_interface = interface.add_mutually_exclusive_group()
    compile_interface.add_argument('-C', '--compile', action='store_true')
    compile_interface.add_argument('--no-compile', dest='compile', action='store_false')

    build_interface = interface.add_mutually_exclusive_group()
    build_interface.add_argument('-B', '--build', action='store_true')
    build_interface.add_argument('--no-build', dest='build', action='store_false')

    force_interface = interface.add_mutually_exclusive_group()
    force_interface.add_argument('-F', '--force', action='store_true')
    force_interface.add_argument('--no-force', dest='force', action='store_false')

    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')

    def run(self) -> None:
        """Buisness logic for building simulation directories from command line."""
        
        if getattr(self, 'options'): 
            return_options(['build', 'simulation'])
            return

        options = {'path', 'name', 'ndim', 'nxb', 'nyb', 'nzb', 'grid', 'python', 'site',
                   'optimize', 'shortcuts', 'flags', 'variables', 'subpath', 'source', 'jobs',
                   'parallelIO', 'compile', 'build', 'force', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        simulation(**local, cmdline=True)
