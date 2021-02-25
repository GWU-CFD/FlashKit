"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os
import sys
import re

# internal libraries
from ...core.error import AutoError
from ...core.logging import printer
from ...core.parallel import single
from ...core.progress import get_bar
from ...core.stream import Instructions, mail
from ...library.create_grid import calc_coords, write_coords
from ...resources import CONFIG, DEFAULTS

# static analysis
if TYPE_CHECKING:
    from typing import Any

# define public interface
__all__ = ['grid', ]

# define default constants (public)
NDIM = DEFAULTS['general']['space']['ndim']
NXB = DEFAULTS['general']['space']['nxb']
NYB = DEFAULTS['general']['space']['nyb']
NZB = DEFAULTS['general']['space']['nzb']
IPROCS = DEFAULTS['general']['mesh']['iprocs']
JPROCS = DEFAULTS['general']['mesh']['jprocs']
KPROCS = DEFAULTS['general']['mesh']['kprocs']
XRANGE = DEFAULTS['general']['space']['xrange']
YRANGE = DEFAULTS['general']['space']['yrange']
ZRANGE = DEFAULTS['general']['space']['zrange']
XMETHOD = DEFAULTS['create']['grid']['xmethod']
YMETHOD = DEFAULTS['create']['grid']['ymethod']
ZMETHOD = DEFAULTS['create']['grid']['zmethod']
PATH: str = DEFAULTS['general']['paths']['working']

# define configuration constants (internal)
AXES = CONFIG['create']['grid']['axes']
BAR_SWITCH = CONFIG['create']['grid']['switch']
NAME = CONFIG['create']['grid']['name']

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # determine arguments passed
    bndbox_given = 'bndbox' in args

    # gather arguments into appropriate tuples
    args['blocks'] = tuple(args[k] for k in ('iprocs', 'jprocs', 'kprocs'))
    args['grids'] = tuple(args[k] for k in ('nxb', 'nyb', 'nzb'))
    args['methods'] = tuple(args[k] for k in ('xmethod', 'ymethod', 'zmethod'))

    # build paramaters dictionary
    args['params'] = {}
    for axis, param in zip(AXES, (args.get(k, {}) for k in ('xparam', 'yparam', 'zparam'))): 
        for key, value in param.items():
            if key in args['params']:
                args['params']['key'][axis] = value
            else:
                args['params']['key'] = {axis: value}

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

    return args

def attach_context(**args: Any) -> dict[str, Any]:
    """Provide a usefull progress bar if appropriate; with throw if some defaults missing."""
    if any(s >= BAR_SWITCH for s in args['grids']) and sys.stdout.isatty():
        args['context'] = get_bar()
    else:
        args['context'] = get_bar(null=True)
        printer.info('Writing grid data out to file ...')
    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    grids: tuple[int, int, int] = args['grids']
    lows: tuple[float, float, float] = args['ranges_low']
    highs: tuple[float, float, float] = args['ranges_high']
    methods: tuple[str, str, str] = args['methods']
    source: str = args['path']
    source = os.path.relpath(source)
    message: str = '\n'.join([
        f'Creating initial grid file from specification:',
        f'  grid_pnts = {grids}',
        f'  sim_range = {lows} -> {highs}',
        f'  algorythm = {methods}',
        f'  grid_file = {source}/{NAME}',
        f'',
        ])
    printer.info(message)
    return args

# default constants for handling the argument stream
PACKAGES = {'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'xrange', 'yrange', 'zrange', 'bndbox',
            'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam', 'path'}
ROUTE = ('create', 'grid')
PRIORITY = {'ignore'}
CRATES = (adapt_arguments, log_messages, attach_context)
DROPS = {'ignore', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'xrange', 'yrange', 'zrange', 'bndbox',
         'xmethod', 'ymethod', 'zmethod', 'xparam', 'yparam', 'zparam'}
MAPPING = {'methods': 'stypes', 'blocks': 'procs', 'ranges_low': 'smins', 'ranges_high': 'smaxs', 'grids': 'sizes'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

def grid(**arguments: Any) -> None:
    """Python application interface for creating a initial grid file from command line or python code.

    Keyword arguments:
    dim: int      Number of simulation dimensions (i.e., 2 or 3); defaults to {create_grid.NDIM}.
    nxb: int      Number of grid points per block in the i direction; defaults to {create_grid.NXB}.
    nyb: int      Number of grid points per block in the j direction; defaults to {create_grid.NYB}.
    nzb: int      Number of grid points per block in the k direction; defaults to {create_grid.NZB}.
    iprocs: int   Number of blocks in the i direction; defaults to {create_grid.IPROCS}.
    jprocs: int   Number of blocks in the j direction; defaults to {create_grid.JPROCS}.
    kprocs: int   Number of blocks in the k direction; defaults to {create_grid.KPROCS}.
    xrange: list  Bounding points (e.g., [0.0, 1.0]) for i direction; defaults to {create_grid.XRANGE}.
    yyange: list  Bounding points (e.g., [0.0, 1.0]) for j direction; defaults to {create_grid.YRANGE}.
    zrange: list  Bounding points (e.g., [0.0, 1.0]) for k direction; defaults to {create_grid.ZRANGE}.
    bndbox: list  Bounding box pairs (e.g., [[0.0, 1.0], ...]) for each of i,j,k directions.
    xmethod: str  Stretching method for grid points in the i directions; defaults to {create_grid.XMETHOD}.
    ymethod: str  Stretching method for grid points in the j directions; defaults to {create_grid.YMETHOD}.
    zmethod: str  Stretching method for grid points in the k directions; defaults to {create_grid.ZMETHOD}.
    xparam: dict  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for i direction method.
    yparam: dict  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for j direction method.
    zparam: dict  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for k direction method.
    path: str     Path to initial grid file; defaults to cwd.
    ignore: bool  Ignore configuration file provided arguments, options, and flags.
    """
    args = process_arguments(**arguments)
    path = args.pop('path')
    with args.pop('context')() as progress:
        write_coords(coords=calc_coords(**args), ndim=args['ndim'], path=path)
