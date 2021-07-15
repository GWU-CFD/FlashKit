"""Create common simulation directory containing specific FLASH job directories"""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ....api.build.jobs import simulation
from ....core.configure import get_defaults
from ....core.custom import patched_error, patched_exceptions
from ....core.options import return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().build.jobs.simulation

PROGRAM = f'flashkit build jobs simulation'

USAGE = f"""\
usage: {PROGRAM} NAME SIMULATION [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
SIMULATION  STRING  Specify a simulation directory contained in the FLASH source/Simulation/SimulationMain.
DIRECTORY   STRING  Specify a directory name; will be determined if not provided.

options:
-?, --???  TYPE  Explaination

flags:
-?, --???  Explaination

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to build simulation directory'

class SimulationJobsApp(Application):
    """Application class for build jobs simulation command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = False
    
    interface.add_argument('simulation', nargs='?')
    interface.add_argument('directory', nargs='?')
    interface.add_argument('-I', '--ignore', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for building jobs simulation directories from command line."""
        
        if self.shared.options: 
            return_options(['build', 'jobs', 'simulation'])
            return
        
        options = {'simulation', 'directory', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        #simulation(**local, cmdline=True)
