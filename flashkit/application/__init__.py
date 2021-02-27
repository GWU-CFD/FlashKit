"""Command-line interface for FlashKit."""

# type annotations
from __future__ import annotations
from typing import Type

# standard libraries
import sys
import argparse

# internal libraries
from ..__meta__ import __version__, __website__
from ..core.logging import logger, DEBUG
from ..core.parallel import force_parallel

# external libraries
from cmdkit.app import Application, ApplicationGroup
from cmdkit.cli import Interface

# command groups
from . import create, build, job

COMMANDS: dict[str, Type[Application]] = {
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

# inject logger back into cmdkit library
Application.log_critical = logger.critical
Application.log_exception =logger.exception

class DebugLogging(argparse.Action):
    """Create custom action for setting debug logging."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        logger.setLevel(DEBUG)
        logger.debug('Set Logging Level To DEBUG!')

class ForceParallel(argparse.Action):
    """Create custom action for setting parallel enviornment."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        force_parallel()

class FlashKit(ApplicationGroup):
    """Application class for flashkit entry-point."""
    ALLOW_PARSE = True
    interface = Interface(PROGRAM, USAGE, HELP)
    interface.add_argument('command')
    interface.add_argument('-v', '--version', version=__version__, action='version')
    interface.add_argument('-V', '--verbose', nargs=0, action=DebugLogging)
    interface.add_argument('-P', '--parallel', nargs=0, action=ForceParallel)
    commands = COMMANDS

def main() -> int:
    """Entry-point for flaskkit command-line interface."""
    return FlashKit.main(sys.argv[1:])
