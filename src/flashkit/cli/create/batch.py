"""Create the appropriate flash execution shell script."""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
#from ...api.create import batch
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_options

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().create.batch

PROGRAM = f'flashkit create batch'

USAGE = f"""\
usage: {PROGRAM} TYPE [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
SITE        STRING  Specify a the site which will determine the shell script to create; defaults to {DEF.site}.

options:
-?, --???  TYPE  Explaination

flags:
-?, --???  Explaination

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to create batch script!'

class BatchCreateApp(Application):
    """Application class for create batch command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True
    
    interface.add_argument('site', nargs='?')
    interface.add_argument('-I', '--ignore', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for creating batch scripts from command line."""
        
        if self.shared.options: 
            return_options(['create', 'batch'])
            return

        options = {'site', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        #batch(**local, cmdline=True)
