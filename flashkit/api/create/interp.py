"""Interpolate an simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import Any, Optional 

# standard libraries
import re
import os
import sys

# internal libraries
from ...core.error import AutoError
from ...core.logging import printer
from ...core.parallel import safe, single, squash
from ...core.progress import get_bar
from ...core.stream import Instructions, mail
from ...library.create_interp import interp_blocks
from ...library.create_grid import read_coords
from ...resources import CONFIG, DEFAULTS
from ...support.grid import get_blocks, get_grids, get_shapes
from ...support.types import Blocks

# external libraries
import numpy

# define public interface
__all__ = ['interp', ]

# define default constants (public)
FIELDS = DEFAULTS['create']['interp']['fields']
GRID = DEFAULTS['general']['files']['grid']
PLOT = DEFAULTS['general']['files']['plot']
IPROCS = DEFAULTS['general']['mesh']['iprocs']
JPROCS = DEFAULTS['general']['mesh']['jprocs']
KPROCS = DEFAULTS['general']['mesh']['kprocs']
NDIM = DEFAULTS['general']['space']['ndim']
NXB = DEFAULTS['general']['space']['nxb']
NYB = DEFAULTS['general']['space']['nyb']
NZB = DEFAULTS['general']['space']['nzb']

# define configuration constants (internal)
GRIDS = CONFIG['create']['block']['grids']
NAME = CONFIG['create']['block']['name']
SWITCH = CONFIG['create']['interp']['switch']
TABLESPAD = CONFIG['create']['interp']['tablespad']
STR_EXCLUDE = re.compile(DEFAULTS['general']['files']['forced'])
STR_INCLUDE = re.compile(DEFAULTS['general']['files']['plot'])

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # determine arguments passed
    if args.get('auto', False):
        step_given = False
        bname_given = False
    else:    
        step_given = 'step' in args.keys()
        bname_given = 'basename' in args.keys()
    
    # resolve proper absolute directory paths
    args['path'] = os.path.realpath(os.path.expanduser(args['path']))
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))
    path = args['path']

    # prepare conditions in order to arrange a list of files to process
    if not step_given or not bname_given:
        listdir = os.listdir(path)
        condition = lambda file: re.search(STR_INCLUDE, file) and not re.search(STR_EXCLUDE, file)

    # find the source file
    if not step_given:
        step = sorted([int(file[-4:]) for file in listdir if condition(file)])[-1]
        if not step:
                raise AutoError(f'Cannot automatically identify simulation file on path {path}')
        args['step'] = step

    # create the basename
    if not bname_given:
        try:
            args['basename'], *_ = next(filter(condition, (file for file in listdir))).split(STR_INCLUDE.pattern)
        except StopIteration:
            raise AutoError(f'Cannot automatically parse basename for simulation files on path {path}')

    # gather arguments into appropriate tuples
    ndim = args['ndim']
    args['procs'] = tuple(args[k] if n < ndim else 1 for n, k in enumerate(('iprocs', 'jprocs', 'kprocs')))
    args['sizes'] = tuple(args[k] if n < ndim else 1 for n, k in enumerate(('nxb', 'nyb', 'nzb')))

    # build flows dictionary
    zloc = GRIDS[-1]
    used = lambda grid: ndim == 3 or grid != zloc
    args['flows'] = {field: (location, *args.get('fsource', {}).get(field, [field, location]))
            for field, location in args['fields'].items() if used(location)}

    return args

def attach_context(**args: Any) -> dict[str, Any]:
    """Provide a usefull progress bar if appropriate; with throw if some defaults missing."""
    if any(s * p >= SWITCH for s, p in zip(args['sizes'], args['procs'])) and sys.stdout.isatty():
        args['context'] = get_bar()
    else:
        args['context'] = get_bar(null=True)
        if False: #args['nofile']:
            printer.info('Interpolating block data (no file out) ...')
        else:
            printer.info('Interpolation block data (out to file) ...')
    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    basename = args['basename']
    dest = os.path.relpath(args['dest'])
    path = os.path.relpath(args['path'])
    step = args['step']
    grid = args['grid']
    plot = args['plot']
    fields = tuple(args['flows'].keys())
    locations = tuple(args['flows'].get(field)[0] for field in fields)
    f_sources = tuple(args['flows'].get(field)[1] for field in fields)
    l_sources = tuple(args['flows'].get(field)[2] for field in fields)
    row = lambda r: '  '.join(f'{e:>{TABLESPAD}}' for e in r) 
    message = '\n'.join([
        f'Creating block file by interpolationg simulation files:',
        f'                  {row(fields)}',
        f'  locations     = {row(locations)}',
        f'  sources       = {row(f_sources)}',
        f'                  {row(l_sources)}',
        f'  plot (source) = {path}/{basename}{plot}{step:04}',
        f'  grid (source) = {path}/{basename}{grid}{0000}',
        f'  block (dest)  = {dest}/{NAME}',
        f'',
        ])
    printer.info(message)
    return args

# default constants for handling the argument stream
PACKAGES = {'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields', 'fsource',
            'basename', 'step', 'plot', 'grid', 'path', 'dest', 'auto'}
ROUTE = ('create', 'interp')
PRIORITY = {'ignore', 'coords'}
CRATES = (adapt_arguments, log_messages, attach_context)
DROPS = {'ignore', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'fields'}
MAPPING = {'grid': 'gridname', 'plot': 'filename'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

@safe
def interp(**arguments: Any) -> None:
    """Python application interface for using interpolation to create an initial block file.

    Keyword arguments:
    ndim: int      Number of final simulation dimensions (i.e., 2 or 3); defaults to {NDIM}.
    nxb: int       Number of final grid points per block in the i direction; defaults to {NXB}.
    nyb: int       Number of final grid points per block in the j direction; defaults to {NYB}.
    nzb: int       Number of final grid points per block in the k direction; defaults to {NZB}.
    iprocs: int    Number of final blocks in the i direction; defaults to {IPROCS}.
    jprocs: int    Number of final blocks in the j direction; defaults to {JPROCS}.
    kprocs: int    Number of final blocks in the k direction; defaults to {KPROCS}.
    fields: dict   Key/value pairs for final fields (e.g., {'velx': 'facex', ...}); defaults are 
                       {FIELDS}.
    fsource: dict  Key/value pairs for source fields (e.g., {'velx': ('cc_u', 'center'), ...}); defaults to FIELDS.
    basename: str  Basename for flash simulation, will be guessed if not provided
                   (e.g., INS_LidDr_Cavity for files INS_LidDr_Cavity_hdf5_plt_cnt_xxxx)
    step: int      File number (e.g., <1,3,5,7,9>) of source timeseries output.
    plot: str      Plot/Checkpoint source file name follower; defaults to '{PLOT}'.
    grid: str      Grid source file name follower; defaults to '{GRID}'.
    path: str      Path to source timeseries hdf5 simulation output files; defaults to cwd.
    dest: str      Path to final grid and block hdf5 files; defaults to cwd.
    ignore: bool   Ignore configuration file provided arguments, options, and flags.
    auto: bool     Force behavior to attempt guessing BASENAME and [--step INT].

    Note:
    By default this function reads the grid data from the hdf5 file (i.e., must run create.grid() first); optionally
    you can provide the result from grid creation directly by using an optional keyword -- coords: (ndarray, ...).
    """
    args = process_arguments(**arguments)
    path = args.pop('dest')
    ndim = args.pop('ndim')
    procs = args.pop('procs')
    sizes = args.pop('sizes')
    coords = args.pop('coords', None)
    
    if coords is None: coords = read_coords(path=path, ndim=ndim)
    shapes = get_shapes(ndim=ndim, procs=procs, sizes=sizes)
    grids = get_grids(coords=coords, ndim=ndim, procs=procs, sizes=sizes)
    centers, boxes = get_blocks(coords=coords, ndim=ndim, procs=procs, sizes=sizes)
    interp_blocks(bndboxes=boxes, centers=centers, dest=path, grids=grids, ndim=ndim, procs=procs, shapes=shapes, **args)
