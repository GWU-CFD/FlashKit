"""Introspect recursively for a desired parameter in flashkit understood files"""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ...api.analyze import where
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().analyze.where

PROGRAM = f'flashkit analyze where'

USAGE = f"""\
usage: {PROGRAM} PARAMETER [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
PARAMETER   STRING  Specify a parameter to recursivly search for.

flags:
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-h, --help           Show this message and exit.

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to search for parameter!'

class WhereAnalyzeApp(Application):
    """Application class for analyze where command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = False
    
    interface.add_argument('parameter', nargs='?')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for analyzing where parameters from command line."""
        
        if getattr(self, 'options'): 
            return_options(['analyze', 'where'])
            return

        options = {'parameter', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        #where(**local, cmdline=True)
