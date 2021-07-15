"""Shepard the porting of FLASH source to a computing resource"""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ...api.build import port
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_available, return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().build.port

PROGRAM = f'flashkit build port'

USAGE = f"""\
usage: {PROGRAM} SITE [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
SITE        STR  Computational resource (e.g., stampede2) desired to port FLASH onto

options:
-?, --???  TYPE  Explaination

flags:
-?, --???  Explaination

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to build port of FLASH!'

class PortBuildApp(Application):
    """Application class for build port command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = False
    
    interface.add_argument('site', nargs='?')
    interface.add_argument('-I', '--ignore', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for building scaling directories from command line."""
        
        if self.shared.options: 
            return_options(['build', 'port'])
            return
        
        if self.shared.available:
            return_available('porting', ['steps'])
            return

        options = {'site', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        #port(**local, cmdline=True)
