"""Create files relavent to flash execution and processing."""

# type annotations
from __future__ import annotations

# internal libraries
from ...core.custom import DictApp

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# commands
from . import block, grid, interp, par, run, xdmf 

COMMANDS: DictApp = {
        'block': block.BlockCreateApp,
        'grid': grid.GridCreateApp,
        'interp': interp.InterpCreateApp,
        'par': par.ParCreateApp,
        'xdmf': xdmf.XdmfCreateApp,
        }

PROGRAM = f'flashkit create'

USAGE = f"""\
usage: {PROGRAM} [-h] <command> [<args>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

commands:   
block       {block.__doc__}
grid        {grid.__doc__}
interp      {interp.__doc__}
par         {par.__doc__}
run         {run.__doc__}
xdmf        {xdmf.__doc__}

options:
-h, --help  Show this message and exit.

Use the -h/--help flag with the above commands to
learn more about their usage.\
"""

class CreateApp(ApplicationGroup):
    """Application class for create command group."""
    
    interface = Interface(PROGRAM, USAGE, HELP)
    commands = COMMANDS
    
    interface.add_argument('command')
