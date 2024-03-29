"""Perform actions related to building flash executables and directories"""

# type annotations
from __future__ import annotations

# internal libraries
from ...core.custom import DictApp

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# commands
from . import jobs, port, scaling, simulation 

COMMANDS: DictApp = {
        'jobs': jobs.JobsBuildApp,
        'port': port.PortBuildApp,
        'scaling': scaling.ScalingBuildApp,
        'simulation': simulation.SimulationBuildApp,
        }

PROGRAM = f'flashkit build'

USAGE = f"""\
usage: {PROGRAM} [-h] <command> [<args>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

commands:   
jobs        {jobs.__doc__}
port        {port.__doc__}
scaling     {scaling.__doc__}
simulation  {simulation.__doc__}

options:
-h, --help  Show this message and exit.

Use the -h/--help flag with the above commands to
learn more about their usage.\
"""

class BuildApp(ApplicationGroup):
    """Application class for build command group."""
    
    interface = Interface(PROGRAM, USAGE, HELP)
    commands = COMMANDS
    
    interface.add_argument('command')
