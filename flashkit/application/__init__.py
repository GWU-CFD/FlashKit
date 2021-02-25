"""Command-line interface for FlashKit."""

# type annotations
from __future__ import annotations
from typing import Type

# standard libraries
import sys
import argparse

# internal libraries
from ..__meta__ import __version__, __website__
from ..core import logging

# external libraries
from cmdkit.app import Application, ApplicationGroup
from cmdkit.cli import Interface

# command groups
from . import create, build, job

COMMANDS: dict[str, Type[Application]] = {'create': create.CreateApp}

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
create              {create.__doc__}
build               {build.__doc__}
job                 {job.__doc__}

options:
-h, --help          Show this message and exit.
-V, --version       Show the version and exit.
-v, --verbose       Enable debug messaging.

files:      (Options are also pulled from files)
../**/flash.toml           Job tree configuration.
./flash.toml               Local configuration.


Use the -h/--help flag with the above commands to
learn more about their usage.

{EPILOG}\
"""

# inject logger back into cmdkit library
Application.log_critical = logging.logger.critical
Application.log_exception = logging.logger.exception

# create custom action for setting debug logging
class DebugLogging(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        logging.logger.setLevel(logging.DEBUG)

class FlashKit(ApplicationGroup):
    """Application class for flashkit entry-point."""
    ALLOW_PARSE = True
    interface = Interface(PROGRAM, USAGE, HELP)
    interface.add_argument('command')
    interface.add_argument('-V', '--version', version=__version__, action='version')
    interface.add_argument('-v', '--verbose', nargs=0, action=DebugLogging)
    commands = COMMANDS

def main() -> int:
    """Entry-point for flaskkit command-line interface."""
    return FlashKit.main(sys.argv[1:])
