"""Create the appropriate flash execution shell script."""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
from ...api.create import batch
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_commands, return_options
from ...core.parse import ListStr
from ...resources import CONFIG

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().create.batch

SKIP = CONFIG['create']['batch']['nosource']

PROGRAM = f'flashkit create batch'

USAGE = f"""\
usage: {PROGRAM} JOB BUILD BASENAME TEMPLATES [<option> VALUE, ...] [<switch>, ...] [<flag>, ...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
JOB         STRING  Specify a job name for the batch execution; will not be determined if not provided. 
BUILD       STRING  Specify a build directory basename; will not be determined if not provided. 
BASENAME    STRING  Basename for flash simulation, will be guessed if not provided
                    (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)
TEMPLATES   LIST    Specify a list of template files (e.g., stampede2) to search for, without the
                    '.toml' extension. These will be combined and used to create the shell script.

options:
-D, --ndim     INT     Number of simulation dimensions (i.e., 2 or 3); defaults to {DEF.ndim}.
-X, --nxb      INT     Number of grid points per block in the i direction; defaults to {DEF.nxb}.
-Y, --nyb      INT     Number of grid points per block in the j direction; defaults to {DEF.nyb}.
-Z, --nzb      INT     Number of grid points per block in the k direction; defaults to {DEF.nzb}.
-i, --iprocs   INT     Number of blocks in the i direction; defaults to {DEF.iprocs}.
-j, --jprocs   INT     Number of blocks in the j direction; defaults to {DEF.jprocs}.
-k, --kprocs   INT     Number of blocks in the k direction; defaults to {DEF.kprocs}.
-n, --ntasks   INT     Number of processors per node (i.e., architecture); defaults to {DEF.ntasks}.
-g, --grid     STRING  Type of FLASH simulation grid used by the Grid Package; defaults to {DEF.grid}.
-b, --source   STRING  Path to the local FLASH source repository; defaults to {DEF.source}.
-l, --launch   STRING  MPI parallel execution command on the machine; defaults to {DEF.launch}.
-s, --sources  LIST    Which library default batch templates to use (use --available to see options);
                       defaults to the {DEF.sources} set of templates.
-p, --path     PATH    Path to simulation files if BASENAME is to be guessed; defaults to cwd.
-d, --dest     PATH    Path to batch file; defaults to cwd.
-f, --hosts  STRING    Hostfile (i.e., node addresses) name; defaults to '{DEF.hosts}'.
-c, --plot   STRING    Plot/Checkpoint file(s) name follower; defaults to '{DEF.plot}'.
-q, --force  STRING    Plot/Checkpoint file(s) substring to ignore; defaults to '{DEF.force}'.
-r, --batch    FILE    Shell script file name follower; defaults to a footer '{DEF.out}'.
-o, --out      FILE    Redirected output file name follower; defaults to a footer '{DEF.out}'.

switches:
-A, --auto       Force behavior to attempt guessing BASENAME.
-B, --find       Use all templates specified in all configuration files.
-C, --redirect   Redirect the console output of the FLASH simulation to a file.
-T, --screen     Use the screen application to fork the FLASH execution from the session.
-H, --hostfile   Use a hostfile in the MPI parallel execution command.
-M, --notasks    Do not specify number of tasks in the MPI parallel execution command.
-N, --nosources  Do not use any library default batch templates.

flags:
-F, --nofile     Do not write the assembled shell commands to file.
-R, --result     Return the formated and assembled shell commands.
-I, --ignore     Ignore configuration file provided arguments, options, and flags.
-O, --options    Show the available options (i.e., defaults and config file format) and exit.
-S, --available  List the available library default batch templates and exit.
-h, --help       Show this message and exit.
"""

# default constants
STR_FAILED = 'Unable to create batch script!'

class BatchCreateApp(Application):
    """Application class for create batch command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True
    
    interface.add_argument('job', nargs='?')
    interface.add_argument('build', nargs='?')
    interface.add_argument('basename', nargs='?')
    interface.add_argument('templates', nargs='?', type=ListStr)

    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int)
    interface.add_argument('-i', '--iprocs', type=int) 
    interface.add_argument('-j', '--jprocs', type=int) 
    interface.add_argument('-k', '--kprocs', type=int) 
    interface.add_argument('-n', '--ntasks', type=int) 
    interface.add_argument('-g', '--grid')
    interface.add_argument('-b', '--source')
    interface.add_argument('-l', '--launch')
    interface.add_argument('-s', '--sources', type=ListStr)
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-f', '--hosts')
    interface.add_argument('-c', '--plot')
    interface.add_argument('-q', '--force')
    interface.add_argument('-r', '--batch')
    interface.add_argument('-o', '--out')

    auto_interface = interface.add_mutually_exclusive_group()
    auto_interface.add_argument('-A', '--auto', action='store_true')
    auto_interface.add_argument('--no-auto', dest='auto', action='store_false')

    find_interface = interface.add_mutually_exclusive_group()
    find_interface.add_argument('-B', '--find', action='store_true')
    find_interface.add_argument('--no-find', dest='find', action='store_false')

    redirect_interface = interface.add_mutually_exclusive_group()
    redirect_interface.add_argument('-C', '--redirect', action='store_true')
    redirect_interface.add_argument('--no-redirect', dest='redirect', action='store_false')

    screen_interface = interface.add_mutually_exclusive_group()
    screen_interface.add_argument('-T', '--screen', action='store_true')
    screen_interface.add_argument('--no-screen', dest='screen', action='store_false')

    hostfile_interface = interface.add_mutually_exclusive_group()
    hostfile_interface.add_argument('-H', '--hostfile', action='store_true')
    hostfile_interface.add_argument('--no-hostfile', dest='hostfile', action='store_false')

    notasks_interface = interface.add_mutually_exclusive_group()
    notasks_interface.add_argument('-M', '--notasks', action='store_true')
    notasks_interface.add_argument('--no-notasks', dest='notasks', action='store_false')

    nosources_interface = interface.add_mutually_exclusive_group()
    nosources_interface.add_argument('-N', '--nosources', action='store_true')
    nosources_interface.add_argument('--no-nosources', dest='nosources', action='store_false')

    interface.add_argument('-F', '--nofile', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    interface.add_argument('-S', '--available', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for creating batch scripts from command line."""
        
        if getattr(self, 'options'): 
            return_options(['create', 'batch'])
            return
        
        if getattr(self, 'available'):
            return_commands(skips=SKIP)
            return

        options = {'job', 'build', 'basename', 'templates', 
                   'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'ntasks', 'grid',
                   'source', 'launch', 'sources', 'path', 'dest', 'hosts', 'plot', 'force', 'batch', 'out',
                   'auto', 'find', 'redirect', 'screen', 'hostfile', 'notasks', 'nosources', 'nofile', 'result', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        batch(**local, cmdline=True)
