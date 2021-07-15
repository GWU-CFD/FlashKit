"""Create common jobs directoy for all FLASH simulations on this site"""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ....api.build.jobs import working
from ....core.configure import get_defaults
from ....core.custom import patched_error, patched_exceptions
from ....core.options import return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().build.jobs.working

PROGRAM = f'flashkit build jobs working'

USAGE = f"""\
usage: {PROGRAM} NAME [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
NAME  STRING  Specify a working FLASH simulation directory; defaults to {DEF.name}.

options:
-?, --???  TYPE  Explaination

flags:
-?, --???  Explaination

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to build working directory'

class WorkingJobsApp(Application):
    """Application class for build jobs working command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = False
    
    interface.add_argument('name', nargs='?')
    interface.add_argument('-I', '--ignore', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for building jobs working directories from command line."""
        
        if self.shared.options: 
            return_options(['build', 'jobs', 'working'])
            return
        
        options = {'name', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        #working(**local, cmdline=True)
