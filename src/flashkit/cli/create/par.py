"""Create an flash parameter file using specified templates and sources."""

# type annotations
from __future__ import annotations

# standard libraries
import logging

# internal libraries
from ...api.create import par
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions
from ...core.options import return_available, return_options
from ...core.parse import DictAny, ListStr
from ...resources import CONFIG

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

logger = logging.getLogger(__name__)

DEF = get_defaults().create.par

SKIP = CONFIG['create']['par']['nosource']

PROGRAM = f'flashkit create par'

USAGE = f"""\
usage: {PROGRAM} TEMPLATES [<option> VALUE, ...] [<switch>, ...] [<flag>, ...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:  
TEMPLATES      LIST  Specify a list of template files (e.g., rayleigh) to search for, without the
                     '.toml' extension. These will be combined and used to create the flash.par file.

options:
-p, --params   DICT  Specific parameters; which are collected in a section at the end of the parameter file.
-s, --sources  LIST  Which library defined sources to use for filling sections from configuration files;
                     defaults to {DEF.sources} --> will fill domain and processor grid parameters).
-d, --dest     PATH  Path to parameter file; defaults to cwd.

switches:
-A, --auto           Force use of all templates specified in all configuration files.
-N, --nosources      Do not use any library specified template sources.
-D, --duplicates     Allow the writing of duplicate parameters if there are multiple matches.
-F, --nofile         Do not write the assembled parameters to file.
-R, --result         Return the formated and assembled parameters.
-I, --ignore         Ignore configuration file provided arguments, options, and flags.

flags:
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-S, --available      List the available library defined sources and exit.
-h, --help           Show this message and exit.

notes:  If duplicates are not allowed, only the most significant instance of a parameter will be written to
        the parameter file, which means the parameter will be based on the depth-first-merge of all relavent 
        templates (and not SOURCES from configuration file variables, which is also the case with --ignore).

        The order of precedence for parameters with potential duplicate entries in ascending order is:
        0) specificed sources retrieved from library defaults
        1) depth-first-merge of specified sources retrieved from a depth-first-merge of configuration files,
        2) depth-first-merge of specified sources in templates (as per 1 above); templates are merged at each level,
        3) depth-first-merge of explicitly specified parameters in templates; templates are merged at each level,
        4) parameters provided at the command line.
"""

# default constants
STR_FAILED = 'Unable to create par file!'

class ParCreateApp(Application):
    """Application class for create par command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)

    ALLOW_NOARGS: bool = True

    interface.add_argument('templates', nargs='?', type=ListStr)
    interface.add_argument('-p', '--params', type=DictAny)
    interface.add_argument('-s', '--sources', type=ListStr)
    interface.add_argument('-d', '--dest')
    interface.add_argument('-A', '--auto', action='store_const', const=True)
    interface.add_argument('-N', '--nosources', action='store_const', const=True)
    interface.add_argument('-D', '--duplicates', action='store_const', const=True)
    interface.add_argument('-F', '--nofile', action='store_const', const=True)
    interface.add_argument('-R', '--result', action='store_const', const=True)
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    interface.add_argument('-S', '--available', action='store_true')

    def run(self) -> None:
        """Buisness logic for creating par from command line."""
        
        if getattr(self, 'options'): 
            return_options(['create', 'par'])
            return

        if getattr(self, 'available'):
            return_available('parameter', ['sources'], SKIP)
            return

        options = {'templates', 'params', 'sources', 'dest', 'auto',
                   'nosources', 'duplicates', 'ignore', 'result', 'nofile'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'cli -- Returned: {local}')
        par(**local, cmdline=True)
