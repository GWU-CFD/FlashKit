"""Create an initial simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations

# internal libraries
from ...api.create import block
from ...core.configure import get_defaults
from ...core.custom import patched_error, patched_exceptions, return_options
from ...core.parse import DictStr, DictDictAny

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface 

DEF = get_defaults().create.block

PROGRAM = f'flashkit create block'

USAGE = f"""\
usage: {PROGRAM} [<opt>...] [<flg>...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

options:
-D, --ndim     INT   Number of simulation dimensions (i.e., 2 or 3); defaults to {DEF.ndim}.
-X, --nxb      INT   Number of grid points per block in the i direction; defaults to {DEF.nxb}.
-Y, --nyb      INT   Number of grid points per block in the j direction; defaults to {DEF.nyb}.
-Z, --nzb      INT   Number of grid points per block in the k direction; defaults to {DEF.nzb}.
-i, --iprocs   INT   Number of blocks in the i direction; defaults to {DEF.iprocs}.
-j, --jprocs   INT   Number of blocks in the j direction; defaults to {DEF.jprocs}.
-k, --kprocs   INT   Number of blocks in the k direction; defaults to {DEF.kprocs}.
-l, --fields   DICT  Key/value pairs for fields (e.g., <temp=center,...>); defaults to 
                         {dict(DEF.fields)}.
-m, --fmethod  DICT  Key/value pairs for flow initialization (e.g., <temp=constant,...>) used for each flow field.
-o, --fparam   DICT  Key/value pairs for paramaters (e.g., <temp={{const=0.5,...}},...>) used for each field method.
-p, --path     PATH  Path to source files used in some initialization methods (e.g., python); defaults to cwd.
-d, --dest     PATH  Path to intial block hdf5 file; defaults to cwd.

flags:
-F, --nofile         Do not write the calculated coordinates to file. 
-R, --result         Return the calculated fields by block on root. 
-I, --ignore         Ignore configuration file provided arguments, options, and flags.
-h, --help           Show this message and exit.

note:  This function reads grid data from an hdf5 file (i.e., must run <flashkit create grid> first); if you receive a cryptic
       error message (e.g., ValueError about inhomogenious shape) make sure you have rerun the create grid command with the 
       correct and compatible options to what you are intending for the create block command.\
"""

# default constants
STR_FAILED = 'Unable to create block file!'

class BlockCreateApp(Application):
    """Application class for create block command."""

    interface = Interface(PROGRAM, USAGE, HELP)
    setattr(interface, 'error', patched_error(STR_FAILED))
    exceptions = patched_exceptions(STR_FAILED)
    
    ALLOW_NOARGS: bool = True

    interface.add_argument('-D', '--ndim', type=int) 
    interface.add_argument('-X', '--nxb', type=int) 
    interface.add_argument('-Y', '--nyb', type=int) 
    interface.add_argument('-Z', '--nzb', type=int) 
    interface.add_argument('-i', '--iprocs', type=int) 
    interface.add_argument('-j', '--jprocs', type=int) 
    interface.add_argument('-k', '--kprocs', type=int) 
    interface.add_argument('-l', '--fields', type=DictStr)
    interface.add_argument('-m', '--fmethod', type=DictStr)
    interface.add_argument('-o', '--fparam', type=DictDictAny)
    interface.add_argument('-p', '--path')
    interface.add_argument('-d', '--dest')
    interface.add_argument('-F', '--nofile', action='store_true')
    interface.add_argument('-R', '--result', action='store_true')
    interface.add_argument('-I', '--ignore', action='store_true')

    def run(self) -> None:
        """Buisness logic for creating block from command line."""
        
        if self.shared.options: 
            return_options('create', 'block')
            return

        options ={'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields', 'fmethod', 'fparam', 
                  'path', 'dest', 'ignore', 'result', 'nofile'}
        local = {key: getattr(self, key) for key in options}
        block(**local, cmdline=True)
