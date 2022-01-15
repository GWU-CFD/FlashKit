"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import Any, Optional 

# standard libraries
import logging
import os
import sys

# internal libraries
from ...core.parallel import safe, single, squash
from ...core.progress import attach_context
from ...core.stream import Instructions, mail
from ...library.create_grid import calc_coords, write_coords
from ...resources import CONFIG, DEFAULTS
from ...support.types import Coords

# external libraries
import numpy

logger = logging.getLogger(__name__)

# define public interface
__all__ = ['grid', ]

# define configuration constants (internal)
AXES = CONFIG['create']['grid']['axes']
COORDS = CONFIG['create']['grid']['coords']
NAME = CONFIG['create']['grid']['name']
LINEWIDTH = CONFIG['create']['grid']['linewidth']
OPTIONPAD = CONFIG['create']['grid']['optionpad']
PRECISION = CONFIG['create']['grid']['precision']

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # determine arguments passed
    bndbox_given = 'bndbox' in args

    # gather arguments into appropriate tuples
    ndim = args['ndim']
    args['procs'] = tuple(args[k] if n < ndim else 1 for n, k in enumerate(('iprocs', 'jprocs', 'kprocs')))
    args['sizes'] = tuple(args[k] if n < ndim else 1 for n, k in enumerate(('nxb', 'nyb', 'nzb')))
    args['methods'] = tuple(args[k] for k in ('xmethod', 'ymethod', 'zmethod'))

    # build paramaters dictionary
    args['params'] = {}
    for axis, param in zip(AXES, (args.get(k, {}) for k in ('xparam', 'yparam', 'zparam'))): 
        for key, value in param.items():
            if key in args['params']:
                args['params'][key][axis] = value
            else:
                args['params'][key] = {axis: value}

    # deal with bounding box of simulation domain
    if bndbox_given and len(args['bndbox']) >= 2 * args['ndim']:
        args['bndbox'] += [None] * (2 * 3 - len(args['bndbox']))
        args['ranges_low'] = tuple(b for b in args['bndbox'][::2])
        args['ranges_high'] = tuple(b for b in args['bndbox'][1::2])
    else:
        args['ranges_low'] = tuple(args[key][0] for key in ('xrange', 'yrange', 'zrange'))
        args['ranges_high'] = tuple(args[key][1] for key in ('xrange', 'yrange', 'zrange'))

    # resolve proper absolute directory paths
    args['path'] = os.path.realpath(os.path.expanduser(args['path']))
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))

    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    user = {'ascii'}
    dest = os.path.relpath(args['dest'])
    ndim = args['ndim'] 
    methods = args['methods'][:ndim]
    params = {kwarg: tuple(f'{value.get(axis, "?"):>{OPTIONPAD}}' for axis in AXES[:ndim]) for kwarg, value in args['params'].items()}
    pad = max((len(key) for key in params.keys()), default=1)
    options = '\n              '.join(f'{k:{pad}}: {v},' for k, v in params.items())
    grids = tuple(s * p if m not in user else '?' for s, p, m in zip(args['sizes'], args['procs'], methods))
    lows = tuple(l if m not in user else '?' for l, m in zip(args['ranges_low'], methods))
    highs = tuple(h if m not in user else '?' for h, m in zip(args['ranges_high'], methods))
    nofile = ' (no file out)' if args['nofile'] else ''
    message = '\n'.join([
        f'\nCreating initial grid file from specification:',
        f'  grid_pnts = {grids}',
        f'  sim_range = {lows} -> {highs}',
        f'  algorythm = {methods}',
        f'  grid_file = {dest}/{NAME}',
        f'  with_opts = {options}',
        f'',
        f'Calculating grid data{nofile} ...',
        ])
    logger.info(message)
    return args

# default constants for handling the argument stream
PACKAGES = {'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'xrange', 'yrange', 'zrange', 'bndbox',
            'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam', 'dest', 'path', 'result', 'nofile'}
ROUTE = ('create', 'grid')
PRIORITY = {'ignore', 'cmdline'}
CRATES = (adapt_arguments, log_messages, attach_context)
DROPS = {'ignore', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'xrange', 'yrange', 'zrange', 'bndbox',
         'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam'}
MAPPING = {'methods': 'stypes', 'ranges_low': 'smins', 'ranges_high': 'smaxs'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

@squash
def screen_out(*, coords: Coords, ndim: int) -> None:
    """Output calculated coordinates to the screen."""
    with numpy.printoptions(precision=PRECISION, linewidth=LINEWIDTH, threshold=numpy.inf):
        message = "\n\n".join(f'{a}:\n{c}' for a, c in zip(COORDS, coords[:ndim]))
        print(f'\nCoordinates are as follows:\n{message}')

@safe
def grid(**arguments: Any) -> Optional[Coords]:
    """Python application interface for creating a initial grid file from command line or python code.

    This method creates an HDF5 file associated with the desired spacial grid specification (on a global
    basis using the face locations), suitable for input by the FLASH application at runtime.

    Keyword Arguments:
        ndim (int):     Number of simulation dimensions (i.e., 2 or 3).
        nxb (int):      Number of grid points per block in the i direction.
        nyb (int):      Number of grid points per block in the j direction.
        nzb (int):      Number of grid points per block in the k direction.
        iprocs (int):   Number of blocks in the i direction.
        jprocs (int):   Number of blocks in the j direction.
        kprocs (int):   Number of blocks in the k direction.
        xrange (list):  Bounding points (e.g., [0.0, 1.0]) for i direction.
        yrange (list):  Bounding points (e.g., [0.0, 1.0]) for j direction.
        zrange (list):  Bounding points (e.g., [0.0, 1.0]) for k direction.
        bndbox (list):  Bounding box pairs (e.g., [0.0, 1.0, ...]) for each of i,j,k directions.
        xmethod (str):  Stretching method for grid points in the i directions.
        ymethod (str):  Stretching method for grid points in the j directions.
        zmethod (str):  Stretching method for grid points in the k directions.
        xparam (dict):  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for i direction method.
        yparam (dict):  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for j direction method.
        zparam (dict):  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for k direction method.
        path (str):     Path to source files used in some stretching methods (e.g., ascii).
        dest (str):     Path to initial grid hdf5 file.
        ignore (bool):  Ignore configuration file provided arguments, options, and flags.
        result (bool):  Return the calculated coordinates.
        nofile (bool):  Do not write the calculated coordinates to file.
    """
    args = process_arguments(**arguments)
    path = args.pop('dest')
    ndim = args['ndim']
    result = args.pop('result')
    nofile = args.pop('nofile')
    cmdline = args.pop('cmdline', False)
    
    with args.pop('context')() as progress:
        coords = calc_coords(**args)
        if not nofile: write_coords(coords=coords, ndim=ndim, path=path)
    
    if not result: return None
    if cmdline: screen_out(coords=coords, ndim=ndim)
    return coords
