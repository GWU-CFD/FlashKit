"""Guided creation of simulation working and job directories"""

# type annotations
from __future__ import annotations

# internal libraries
from ....core.custom import DictApp

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# commands
from . import collection, job, simulation, working

COMMANDS: DictApp = {
        'collection': collection.CollectionJobsApp,
        'job': job.JobJobsApp,
        'simulation': simulation.SimulationJobsApp,
        'working': working.WorkingJobsApp,
        }

PROGRAM = f'flashkit build jobs'

USAGE = f"""\
usage: {PROGRAM} [-h] <command> [<args>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

commands:   
working     {working.__doc__}
collection  {collection.__doc__}
simulation  {simulation.__doc__}
job         {job.__doc__}

options:
-h, --help  Show this message and exit.

Use the -h/--help flag with the above commands to
learn more about their usage.\
"""

class JobsBuildApp(ApplicationGroup):
    """Application class for build jobs command group."""

    interface = Interface(PROGRAM, USAGE, HELP)
    commands = COMMANDS
    
    interface.add_argument('command')
