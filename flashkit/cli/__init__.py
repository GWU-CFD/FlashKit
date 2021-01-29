"""Command-line interface for FlashKit."""

# standard libraries
import sys

# internal libraries
from ..__meta__ import __version__, __website__

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# command groups
from . import create, build, job

COMMANDS = {
    'create': create.CreateApp,
#    'build': build.BuildApp,
#    'job': job.JobApp
}

PROGRAM = f'flashkit'

USAGE = f"""\
usage: flashkit [-h] [-v] <command> [<args>...]
Command-line tools for FlashKit.\
"""

EPILOG = f"""\
Documentation and issue tracking at:
{__website__}\
"""

HELP = f"""\
{USAGE}
    
commands:
create              {create.__doc__}
build               {build.__doc__}
job                 {job.__doc__}

options:
-h, --help          Show this message and exit.
-v, --version       Show the version and exit.

Use the -h/--help flag with the above commands to
learn more about their usage.

{EPILOG}\
"""

class FlashKit(ApplicationGroup):
    """Application class for flashkit entry-point."""

    interface = Interface(PROGRAM, USAGE, HELP)
    interface.add_argument('-v', '--version', version=__version__, action='version')
    interface.add_argument('command')

    command = None
    commands = COMMANDS

def main() -> int:
    """Entry-point for flaskkit command-line interface."""
    return FlashKit.main(sys.argv[1:])
