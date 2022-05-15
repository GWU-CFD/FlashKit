"""construct the directories, files, and scripts for strong/weak scaling analysis"""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ...api.build import scaling
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().build.scaling

PROGRAM = f'flashkit build scaling'

USAGE = f"""\
usage: {PROGRAM} [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

flags:
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-h, --help           Show this message and exit.

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to build scaling directories!'

class ScalingBuildApp(Application):
    """Application class for build scaling command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True
    
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for building scaling directories from command line."""
        
        if getattr(self, 'options'): 
            return_options(['build', 'scaling'])
            return

        options = {'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'Command -- Entry point for scaling command.')
        #scaling(**local, cmdline=True)
