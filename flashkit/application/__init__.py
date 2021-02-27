"""Command-line interface for FlashKit."""

# type annotations
from __future__ import annotations
from typing import Type

# standard libraries
import sys

# internal libraries
from ..__meta__ import __version__, __website__
from ..core.custom import DebugLogging, ForceParallel, DictApp

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# command groups
from . import create, build, job

COMMANDS: DictApp = {
        'create': create.CreateApp,
        }

PROGRAM = f'flashkit'

USAGE = f"""\
usage: flashkit [-h] [-v] [-V] <command> [<args>...]
Command-line tools for FlashKit.\
"""

EPILOG = f"""\
Documentation and issue tracking at:
{__website__}\
"""

HELP = f"""\
{USAGE}
    
commands:
create       {create.__doc__}
build        {build.__doc__}
job          {job.__doc__}

options:
-h, --help        Show this message and exit.
-v, --version     Show the version and exit.
-V, --verbose     Enable debug messaging.
-P, --parallel    Indicate Parallel execution, useful for when flashkit
                    is executed from a job script and cannot determine 
                    its parallel or serial execution status automatically.

files:              (Options are also pulled from files)
../**/flash.toml    Job tree configuration.
./flash.toml        Local configuration.

Use the -h/--help flag with the above commands to
learn more about their usage.

{EPILOG}\
"""

class FlashKit(ApplicationGroup):
    """Application class for flashkit entry-point."""
   
    interface = Interface(PROGRAM, USAGE, HELP)
    commands = COMMANDS
    
    ALLOW_PARSE = True

    interface.add_argument('command')
    interface.add_argument('-v', '--version', version=__version__, action='version')
    interface.add_argument('-V', '--verbose', nargs=0, action=DebugLogging)
    interface.add_argument('-P', '--parallel', nargs=0, action=ForceParallel)

def main() -> int:
    """Entry-point for flaskkit command-line interface."""
    return FlashKit.main(sys.argv[1:])
