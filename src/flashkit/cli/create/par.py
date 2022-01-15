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
-p, --params   DICT  Specific parameters; which are collected into a single section of the parameter file.
-s, --sources  LIST  Which library default parameter templates to use (use --available to see options);
                     defaults to the {DEF.sources} set of templates.
-d, --dest     PATH  Path to parameter file; defaults to cwd.

switches:
-A, --auto           Use all templates specified in all configuration files.
-N, --nosources      Do not use any library default parameter templates.
-D, --duplicates     Allow the writing of duplicate parameters if there are multiple matches.

flags:
-F, --nofile         Do not write the assembled parameters to file.
-R, --result         Return the formated and assembled parameters.
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-O, --options        Show the available options (i.e., defaults and config file format) and exit.
-S, --available      List the available library default parameter templates and exit.
    --advanced       Include all defined templates when showing library default templates.
-h, --help           Show this message and exit.

notes:  If duplicates are not allowed, only the most significant instance of a parameter will be written to
        the parameter file, which means the parameter will be based on the depth-first-merge of all relavent 
        templates and resolved sources from defaults, configuration files, and provided options.

        The order of precedence for parameters with potential duplicate entries in ascending order is.
        0) depth-first-merge of defaults, configuration files, and provided options; resolution of sourced parameters,
        1) parameters retrieved from specified library default parameter templates,
        2) duplicate parameters of the same type in the same template file are ignored,
        3) duplicate parameters of different types in the same template file are ordered as sources < sinks < explicite 
        4) duplicate parameters of any type in different template files within the same folder are orderd as the specified templates,
        5) duplicate parameters of any type in any template files from a deeper folder in the folder tree,
        6) explicite parameters provided at the command line.
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

    auto_interface = interface.add_mutually_exclusive_group()
    auto_interface.add_argument('-A', '--auto', action='store_const', const=True)
    auto_interface.add_argument('--no-auto', dest='auto', action='store_const', const=False)
 
    nosources_interface = interface.add_mutually_exclusive_group()
    nosources_interface.add_argument('-N', '--nosources', action='store_const', const=True)
    nosources_interface.add_argument('--no-nosources', dest='nosources', action='store_const', const=False)

    duplicates_interface = interface.add_mutually_exclusive_group()
    duplicates_interface.add_argument('-D', '--duplicates', action='store_const', const=True)
    duplicates_interface.add_argument('--no-duplicates', dest='duplicates', action='store_const', const=False)

    interface.add_argument('-F', '--nofile', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')
    interface.add_argument('-O', '--options', action='store_true')
    interface.add_argument('-S', '--available', action='store_true')
    interface.add_argument('--advanced', action='store_true')

    def run(self) -> None:
        """Buisness logic for creating par from command line."""
        
        if getattr(self, 'options'): 
            return_options(['create', 'par'])
            return

        if getattr(self, 'available'):
            if getattr(self, 'advanced'):
                return_available(category='parameter', tags=['sources', 'sinks'])
            else:
                return_available(category='parameter', tags=['sources'], skips=SKIP)
            return

        options = {'templates', 'params', 'sources', 'dest', 'auto',
                   'nosources', 'duplicates', 'ignore', 'result', 'nofile'}
        local = {key: getattr(self, key) for key in options}
        logger.debug(f'Command -- Entry point for par command.')
        par(**local, cmdline=True)
