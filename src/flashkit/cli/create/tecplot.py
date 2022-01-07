"""Create a tecplot readable files associated with flash simulation HDF5 output."""

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

DEF = get_defaults().create.tecplot

PROGRAM = f'flashkit create tecplot'

USAGE = f"""\
usage: {PROGRAM} BASENAME [<flag>, ...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
BASENAME     STRING  Basename for flash simulation, will be guessed if not provided
                     (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)

flags:
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-h, --help           Show this message and exit.

note: This operation is not currently implemented in this version of FlashKit
"""

# default constants
STR_FAILED = 'Unable to create tecplot files!'

class TecplotCreateApp(Application):
    """Application class for create tecplot command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True
    
    interface.add_argument('basename', nargs='?')
    
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    
    def run(self) -> None:
        """Buisness logic for creating tecplot files from command line."""
        
        if getattr(self, 'options'): 
            return_options(['create', 'tecplot'])
            return

        options = {'basename', 'ignore'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        #tecplot(**local, cmdline=True)
