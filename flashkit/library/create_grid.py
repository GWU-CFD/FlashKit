"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import cast, TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..core.parallel import safe, squash
from ..resources import CONFIG 
from ..support.stretch import Stretching, Parameters 

# external libraries
import numpy 
import h5py  # type: ignore

# static analysis
if TYPE_CHECKING:
    from typing import Any, Dict, Tuple
    from collections.abc import MutableSequence, Sequence, Sized
    N = numpy.ndarray
    M = MutableSequence[N]
    Coords = Tuple[N, N, N]
    Blocks = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]]

# define library (public) interface
__all__ = ['calc_coords', 'get_blocks', 'get_shapes', 'write_coords', ]

# define configuration constants (internal)
DIRECTIONS = CONFIG['create']['grid']['axes']
LABEL = CONFIG['create']['grid']['label']
NAME = CONFIG['create']['grid']['name']

@safe
def calc_coords(*, ndim: int, params: dict[str, dict[str, Any]], procs: tuple[int, int, int], 
                smins: tuple[float, float, float], smaxs: tuple[float, float, float], 
                sizes: tuple[int, int, int], stypes: tuple[str, str, str]) -> Coords:
    """Calculate global coordinate axis arrays; face data vice cell data."""

    # create grid init parameters
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_min, gr_max = numpy.array(smins, float), numpy.array(smaxs, float)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)

    # create grid stretching parameters
    gr_str = Stretching(stypes, Parameters(**params))

    # Create grids
    return get_filledCoords(sizes=gr_gIndexSize, methods=gr_str, ndim=ndim, smin=gr_min, smax=gr_max)

@safe
def get_blocks(*, coords: Coords, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Blocks:
    """Calculate block coordinate axis arrays from global axis arrays."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)
    xfaces, yfaces, zfaces = coords

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
def get_shapes(*, procs: tuple[int , int, int], sizes: tuple[int, int, int]) -> dict[str, tuple[int, ...]]:
    """Determine shape of simulation data on the relavent grids (e.g., center or facex)."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)
   
    # create shape data as dictionary
    shapes = {'center': tuple([gr_axisNumProcs.prod()] + gr_lIndexSize[::-1].tolist())}
    shapes['facex'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 0, 1))) 
    shapes['facey'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 1, 0))) 
    shapes['facez'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (1, 0, 0))) 
    
    return shapes

@squash
def write_coords(*, coords: Coords, ndim: int, path: str) -> None:
    """Write global coordinate axis arrays to an hdf5 file."""
    filename = path + NAME
    with h5py.File(filename, 'w') as h5file:
        for axis, coord in zip(DIRECTIONS[:ndim], coords[:ndim]):
            if coord is not None:
                h5file.create_dataset(axis + LABEL, data=coord)

def create_indexSize_fromGlobal(i: int, j: int, k: int, ijkProcs: N) -> tuple[N, N]:
    gSizes = numpy.array([i, j, k], int)
    blocks = numpy.array([size / procs for procs, size in zip(ijkProcs, gSizes)], int)
    return blocks, gSizes

def create_indexSize_fromLocal(i: int, j: int, k: int, ijkProcs: N) -> tuple[N, N]:
    blocks = numpy.array([i, j, k], int)
    gSizes = numpy.array([procs * nb for procs, nb in zip(ijkProcs, blocks)], int)
    return blocks, gSizes

def create_processor_grid(iProcs: int, jProcs: int, kProcs: int) -> tuple[N, N]:
    proc = numpy.array([iProcs, jProcs, kProcs], int)
    grid = numpy.array([[i, j, k] for k in range(kProcs) for j in range(jProcs) for i in range(iProcs)], int)
    return proc, grid

def get_filledCoords(*, sizes: N, methods: Stretching, ndim: int, smin: N, smax: N) -> Coords:
    coords: M = cast(M, [None, None, None])
    for method, func in methods.stretch.items():
        if methods.any_axes(method):
            func(axes=methods.map_axes(method), coords=coords, sizes=sizes, ndim=ndim, smin=smin, smax=smax)
    x, y, z = coords
    return x, y, z
