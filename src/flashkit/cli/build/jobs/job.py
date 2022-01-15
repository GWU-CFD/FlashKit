"""Create FLASH simulation (job) directory"""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ....api.build.jobs import job
from ....core.configure import get_defaults
from ....core.custom import patched_error, patched_exceptions
from ....core.options import return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().build.jobs.job

PROGRAM = f'flashkit build jobs job'

USAGE = f"""\
usage: {PROGRAM} NAME [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
NAME  STRING  Specify a FLASH simulation (i.e., directory name).

flags:
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-h, --help           Show this message and exit.

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to build job directory'

class JobJobsApp(Application):
    """Application class for build jobs job command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = False
    
    interface.add_argument('name', nargs='?')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for building jobs job directories from command line."""
        
        if getattr(self, 'options'): 
            return_options(['build', 'jobs', 'job'])
            return
        
        options = {'name', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'Command -- Entry point for job command.')
        #job(**local, cmdline=True)
