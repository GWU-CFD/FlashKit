"""Create an initial simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import Any, Optional 

# standard libraries
import logging
import os
import sys

# internal libraries
from ...core.parallel import safe, single, squash
from ...core.progress import get_bar
from ...core.stream import Instructions, mail
from ...library.create_block import calc_blocks, write_blocks
from ...library.create_grid import read_coords
from ...resources import CONFIG, DEFAULTS
from ...support.grid import get_grids, get_shapes
from ...support.types import Blocks

# external libraries
import numpy

logger = logging.getLogger(__name__)

# define public interface
__all__ = ['block', ]

# define configuration constants (internal)
GRIDS = CONFIG['create']['block']['grids']
METHOD = CONFIG['create']['block']['method']
SWITCH = CONFIG['create']['block']['switch']
NAME = CONFIG['create']['block']['name']
LINEWIDTH = CONFIG['create']['block']['linewidth']
OPTIONPAD = CONFIG['create']['block']['optionpad']
TABLESPAD = CONFIG['create']['block']['tablespad']
PRECISION = CONFIG['create']['block']['precision']

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # gather arguments into appropriate tuples
    ndim = args['ndim']
    args['procs'] = tuple(args[k] if n < ndim else 1 for n, k in enumerate(('iprocs', 'jprocs', 'kprocs')))
    args['sizes'] = tuple(args[k] if n < ndim else 1 for n, k in enumerate(('nxb', 'nyb', 'nzb')))

    # build flows dictionary
    zloc = GRIDS[-1]
    used = lambda grid: ndim == 3 or grid != zloc
    args['flows'] = {field: (location, args.get('fmethod', {}).get(field, METHOD)) 
            for field, location in args['fields'].items() if used(location)}

    # build paramaters dictionary
    args['params'] = {}
    for field, param in args.get('fparam', {}).items(): 
        for key, value in param.items():
            if key in args['params']:
                args['params'][key][field] = value
            else:
                args['params'][key] = {field: value}

    # resolve proper absolute directory paths
    args['path'] = os.path.realpath(os.path.expanduser(args['path']))
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))

    return args

def attach_context(**args: Any) -> dict[str, Any]:
    """Provide a usefull progress bar if appropriate; with throw if some defaults missing."""
    noattach = not any(s * p >= SWITCH for s, p in zip(args['sizes'], args['procs'])) and sys.stdout.isatty()
    args['context'] = get_bar(null=noattach)
    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    dest = os.path.relpath(args['dest'])
    fields = tuple(args['flows'].keys())
    locations = tuple(args['flows'].get(field)[0] for field in fields)
    methods = tuple(args['flows'].get(field)[1] for field in fields)
    params = {kwarg: tuple(f'{value.get(field, "?"):>{OPTIONPAD}}' for field in fields) for kwarg, value in args['params'].items()}
    pad = max((len(key) for key in params.keys()), default=1)
    options = '\n               '.join(f'{k:{pad}}: {v},' for k, v in params.items())
    row = lambda r: '  '.join(f'{e:>{TABLESPAD}}' for e in r) 
    nofile = ' (no file out)' if args['nofile'] else ''
    message = '\n'.join([
        f'Creating initial block file from specification:',
        f'               {row(fields)}',
        f'  locations  = {row(locations)}',
        f'  algorythm  = {row(methods)}',
        f'  block_file = {dest}/{NAME}',
        f'  with_opts  = {options}',
        f'',
        f'  Calculating block data{nofile} ...',
        ])
    logger.info(message)
    return args

# default constants for handling the argument stream
PACKAGES = {'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields', 'fmethod', 'fparam', 'dest', 'path', 'result', 'nofile'}
ROUTE = ('create', 'block')
PRIORITY = {'ignore', 'cmdline', 'coords'}
CRATES = (adapt_arguments, log_messages, attach_context)
DROPS = {'ignore', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields', 'fmethod', 'fparam'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

@squash
def screen_out(*, blocks: Blocks) -> None:
    """Output calculated fields by block to the screen."""
    with numpy.printoptions(precision=PRECISION, linewidth=LINEWIDTH, threshold=numpy.inf):
        message = "\n\n".join(f'{f}:\n{b}' for f, b in blocks.items())
        print(f'\nFields for blocks on root are as follows:\n{message}')

@safe
def block(**arguments: Any) -> Optional[Blocks]:
    """Python application interface for creating an initial block file from command line or python code.

    This method creates an HDF5 file associated with the desired intial flow specification (for each
    needed computational field), suitable for input by the FLASH application at runtime.

    Keyword Arguments:
        ndim (int):      Number of simulation dimensions (i.e., 2 or 3).
        nxb (int):       Number of grid points per block in the i direction.
        nyb (int):       Number of grid points per block in the j direction.
        nzb (int):       Number of grid points per block in the k direction.
        iprocs (int):    Number of blocks in the i direction.
        jprocs (int):    Number of blocks in the j direction.
        kprocs (int):    Number of blocks in the k direction.
        fields (dict):   Key/value pairs for fields (e.g., {'temp': 'center', ...})
        fmethod (dict):  Key/value pairs for flow initialization (e.g., {'temp': 'constant', ...}).
        fparam (dict):   Key/value pairs for paramaters (e.g., {'temp': {'const': 0.5, ...}, ...}) used for each field method.
        path (str):      Path to source files used in some initialization methods (e.g., python).
        dest (str):      Path to initial block hdf5 file.
        ignore (bool):   Ignore configuration file provided arguments, options, and flags.
        result (bool):   Return the calculated fields by block on root.
        nofile (bool):   Do not write the calculated fields by block to file.

    Note:
        By default this function reads the grid data from the hdf5 file (i.e., must run create.grid() first); optionally
        you can provide the result from grid creation directly by using an optional keyword -- coords: (ndarray, ...).
    """
    args = process_arguments(**arguments)
    path = args.pop('dest')
    ndim = args.pop('ndim')
    procs = args.pop('procs')
    sizes = args.pop('sizes')
    result = args.pop('result')
    nofile = args.pop('nofile')
    cmdline = args.pop('cmdline', False)
    coords = args.pop('coords', None)
    
    with args.pop('context')() as progress:
        if coords is None: coords = read_coords(path=path, ndim=ndim)
        shapes = get_shapes(ndim=ndim, procs=procs, sizes=sizes)
        grids = get_grids(coords=coords, ndim=ndim, procs=procs, sizes=sizes) 
        blocks, index = calc_blocks(grids=grids, procs=procs, shapes=shapes, **args)
        if not nofile: write_blocks(blocks=blocks, index=index, path=path, shapes=shapes)
    
    if not result: return None
    if cmdline: screen_out(blocks=blocks)
    return blocks
