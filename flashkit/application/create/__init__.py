"""Create files relavent to flash execution and processing."""

# external libraries
from cmdkit.app import ApplicationGroup
from cmdkit.cli import Interface

# commands
from . import xdmf, par, run, init

COMMANDS = {
    'xdmf': xdmf.XdmfCreateApp,
#    'par': par.ParCreateApp,
#    'run': run.RunCreateApp,
#    'init': init.InitCreateApp,
}

PROGRAM = f'flashkit create'

USAGE = f"""\
usage: {PROGRAM} [-h] <command> [<args>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

commands:
xdmf                {xdmf.__doc__}
par                 {par.__doc__}
run                 {run.__doc__}
init                {init.__doc__}

options:
-h, --help          Show this message and exit.

files:
~/.flashkit/config.toml    User configuration.
../**/flash.toml           Job tree configuration.
./flash.toml               Local configuration.

Use the -h/--help flag with the above commands to
learn more about their usage.\
"""

class CreateApp(ApplicationGroup):
    """Application class for create command group."""

    interface = Interface(PROGRAM, USAGE, HELP)
    
    command = None
    interface.add_argument('command')

    commands = COMMANDS
