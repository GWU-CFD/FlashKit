"""Introspect simulation directories and analyze results simulation jobs""" 

# type annotations
from __future__ import annotations

# internal libraries
from ...core.custom import DictApp

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# commands
from . import where 

COMMANDS: DictApp = {
        'where': where.WhereAnalyzeApp,
        }

PROGRAM = f'flashkit analyze'

USAGE = f"""\
usage: {PROGRAM} [-h] <command> [<args>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

commands:   
where        {where.__doc__}

options:
-h, --help  Show this message and exit.

Use the -h/--help flag with the above commands to
learn more about their usage.\
"""

class AnalyzeApp(ApplicationGroup):
    """Application class for analyze command group."""
    
    interface = Interface(PROGRAM, USAGE, HELP)
    commands = COMMANDS
    
    interface.add_argument('command')
