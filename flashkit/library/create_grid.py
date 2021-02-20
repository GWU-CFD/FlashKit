"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import cast, TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..core.parallel import safe, squash
from ..resources import CONFIG, DEFAULTS 
from ..support.stretch import Stretching, Parameters 

# external libraries
import numpy 
import h5py  # type: ignore

# static analysis
if TYPE_CHECKING:
    from typing import Any, Tuple
    from collections.abc import MutableSequence, Sized
    N = numpy.ndarray
    M = MutableSequence[N]
    Coords = Tuple[N, N, N]
    Blocks = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]] 

# define public interface
__all__ = ['calc_coords', 'get_blocks', 'get_shapes', 'write_coords', ]

# define default constants
PATH = DEFAULTS['general']['paths']['working']
NDIM = DEFAULTS['create']['grid']['ndim']
SIZE = DEFAULTS['create']['grid']['size']
SMIN = DEFAULTS['create']['grid']['smin']
SMAX = DEFAULTS['create']['grid']['smax']

# define configuration constants
AXES = tuple(CONFIG['create']['grid']['axes'])
DIRECTIONS = tuple(CONFIG['create']['grid']['axes'])
LABEL = CONFIG['create']['grid']['label']
MDIM = CONFIG['create']['grid']['mdim']
METHOD = CONFIG['create']['grid']['method']
NAME = CONFIG['create']['grid']['name']

@safe
def calc_coords(*, param: dict[str, dict[str, Any]] = {}, procs: dict[str, int] = {},
                simmn: dict[str, float] = {}, simmx: dict[str, float] = {}, sizes: dict[str, int] = {}, 
                stype: dict[str, str] = {}, ndims: int = NDIM) -> Coords:
    """Calculate global coordinate axis arrays; face data vice cell data."""

    # create grid init parameters
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(**procs)
    gr_min, gr_max = create_bounds(mins=simmn, maxs=simmx)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(**sizes, ijkProcs=gr_axisNumProcs)
    gr_ndim = ndims

    # create grid stretching parameters
    gr_strBool, gr_strType = create_stretching(methods=stype)
    gr_str = Stretching(gr_strType, Parameters(**param))

    # Create grids
    x, y, z = get_filledCoords(sizes=gr_gIndexSize, methods=gr_str, ndim=gr_ndim, smin=gr_min, smax=gr_max)
    return x, y, z

@safe
def get_blocks(coordinates: Coords, *, procs: dict[str, int] = {}, sizes: dict[str, int] = {}) -> Blocks:
    """Calculate block coordinate axis arrays from global axis arrays."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(**procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(**sizes, ijkProcs=gr_axisNumProcs)
    xfaces, yfaces, zfaces = coordinates

    # calculate the iaxis block coordinates
    lIndex = gr_lIndexSize[0]
    xxxl = numpy.array([xfaces[0 + i * lIndex:0 + (i + 1) * lIndex] for i, _, _ in gr_axisMesh])
    xxxr = numpy.array([xfaces[1 + i * lIndex:1 + (i + 1) * lIndex] for i, _, _ in gr_axisMesh])
    xxxc = (xxxr + xxxl) / 2.0

    # calculate the jaxis block coordinates
    lIndex = gr_lIndexSize[1]
    yyyl = numpy.array([yfaces[0 + j * lIndex:0 + (j + 1) * lIndex] for _, j, _ in gr_axisMesh])
    yyyr = numpy.array([yfaces[1 + j * lIndex:1 + (j + 1) * lIndex] for _, j, _ in gr_axisMesh])
    yyyc = (yyyr + yyyl) / 2.0

    # calculate the kaxis block coordinates
    if zfaces is not None:
        lIndex = gr_lIndexSize[2]
        zzzl = numpy.array([zfaces[0 + k * lIndex:0 + (k + 1) * lIndex] for _, _, k in gr_axisMesh])
        zzzr = numpy.array([zfaces[1 + k * lIndex:1 + (k + 1) * lIndex] for _, _, k in gr_axisMesh])
        zzzc = (zzzr + zzzl) / 2.0
    else:
        zzzl, zzzr, zzzc = None, None, None

    return (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr)

@safe
def get_shapes(*, procs: dict[str, int] = {}, sizes: dict[str, int] = {}) -> dict[str, tuple[int, ...]]:
    """Determine shape of simulation data on the relavent grids (e.g., center or facex)."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(**procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(**sizes, ijkProcs=gr_axisNumProcs)
   
    # create shape data as dictionary
    shapes = {'center': tuple([gr_axisNumProcs.prod()] + gr_lIndexSize[::-1].tolist())}
    shapes['facex'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 0, 1))) 
    shapes['facey'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 1, 0))) 
    shapes['facez'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (1, 0, 0))) 
    
    return shapes

@squash
def write_coords(coordinates: tuple[N, N, N], *, path: str = PATH) -> None:
    """Write global coordinate axis arrays to an hdf5 file."""
    filename = path + NAME
    with h5py.File(filename, 'w') as file:
        for axis, coords in zip(DIRECTIONS, coordinates):
            if coords is not None:
                file.create_dataset(axis + LABEL, data=coords)

def create_bounds(*, mins: dict[str, float]={}, maxs: dict[str, float]={}) -> tuple[N, N]:
    def_mins = {key: SMIN for key in AXES}
    def_maxs = {key: SMAX for key in AXES}
    simmn = numpy.array([mins.get(key, default) for key, default in def_mins.items()], float)
    simmx = numpy.array([maxs.get(key, default) for key, default in def_maxs.items()], float)
    return simmn, simmx

def create_indexSize_fromGlobal(*, i: int = SIZE, j: int = SIZE, k: int = SIZE, ijkProcs: N) -> tuple[N, N]:
    gSizes = numpy.array([i, j, k], int)
    blocks = numpy.array([size / procs for procs, size in zip(ijkProcs, gSizes)], int)
    return blocks, gSizes

def create_indexSize_fromLocal(*, i: int = SIZE, j: int = SIZE, k: int = SIZE, ijkProcs: N) -> tuple[N, N]:
    blocks = numpy.array([i, j, k], int)
    gSizes = numpy.array([procs * nb for procs, nb in zip(ijkProcs, blocks)], int)
    return blocks, gSizes

def create_processor_grid(*, i: int = SIZE, j: int = SIZE, k: int = SIZE) -> tuple[N, N]:
    iProcs, jProcs, kProcs = i, j, k
    proc = numpy.array([iProcs, jProcs, kProcs], int)
    grid = numpy.array([[i, j, k] for k in range(kProcs) for j in range(jProcs) for i in range(iProcs)], int)
    return proc, grid

def create_stretching(*, methods: dict[str, str] = {}) -> tuple[list[bool], list[str]]:
    default = METHOD
    def_methods = {key: default for key in AXES}
    strTypes = [methods.get(key, default) for key, default in def_methods.items()]
    strBools = [method != default for method in strTypes]
    return strBools, strTypes

def get_blankCoords(sizes: Sized) -> list[None]:
    return [None] * len(sizes)

def get_filledCoords(*, sizes: N, methods: Stretching, ndim: int, smin: N, smax: N) -> M:
    coords: M = cast(M, get_blankCoords(sizes))

    for method, func in methods.stretch.items():
        if methods.any_axes(method):
            func(axes=methods.map_axes(method), coords=coords, sizes=sizes, ndim=ndim, smin=smin, smax=smax)

    return coords
