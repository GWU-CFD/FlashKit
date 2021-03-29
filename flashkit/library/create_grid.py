"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import cast, TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..core.parallel import Index, safe, single, squash
from ..resources import CONFIG 
from ..support.stretch import Stretching

# external libraries
import numpy 
import h5py  # type: ignore

# static analysis
if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Tuple
    from collections.abc import MutableSequence, Sequence, Sized
    N = numpy.ndarray
    M = MutableSequence[N]
    Coords = Tuple[N, N, N]
    Faces = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]]
    Grids = Dict[str, Tuple[Optional[N], ...]]
    Shapes = Dict[str, Tuple[int, ...]]

# deal w/ runtime cast
else:
    M = None

# define library (public) interface
__all__ = ['calc_coords', 'get_faces', 'get_grids', 'get_shapes', 'read_coords', 'write_coords', ]

# define configuration constants (internal)
AXES = CONFIG['create']['grid']['coords']
LABEL = CONFIG['create']['grid']['label']
NAME = CONFIG['create']['grid']['name']

@safe
def calc_coords(*, ndim: int, params: dict[str, dict[str, Any]], path: str, procs: tuple[int, int, int], 
                smins: tuple[float, float, float], smaxs: tuple[float, float, float], 
                sizes: tuple[int, int, int], stypes: tuple[str, str, str]) -> Coords:
    """Calculate global coordinate axis arrays; face data vice cell data."""

    # create grid init parameters
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_min, gr_max = numpy.array(smins, float), numpy.array(smaxs, float)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)

    # create grid stretching parameters
    gr_str = Stretching(stypes, path, **params)

    # Create grids
    return get_filledCoords(sizes=gr_gIndexSize, methods=gr_str, ndim=ndim, smin=gr_min, smax=gr_max)

@safe
def get_faces(*, coords: Coords, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Faces:
    """Calculate block (by process mesh) coordinate axis arrays from global axis arrays for each face."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)
    xfaces, yfaces, zfaces = coords
    
    # calculate the iaxis block coordinates
    lIndex, lRange = gr_lIndexSize[0], range(gr_axisNumProcs[0])
    xxxl = numpy.array([xfaces[0 + i * lIndex:0 + (i + 1) * lIndex] for i in lRange], dtype=float)
    xxxr = numpy.array([xfaces[1 + i * lIndex:1 + (i + 1) * lIndex] for i in lRange], dtype=float)
    xxxc = (xxxr + xxxl) / 2.0

    # calculate the jaxis block coordinates
    lIndex, lRange = gr_lIndexSize[1], range(gr_axisNumProcs[1])
    yyyl = numpy.array([yfaces[0 + j * lIndex:0 + (j + 1) * lIndex] for j in lRange], dtype=float)
    yyyr = numpy.array([yfaces[1 + j * lIndex:1 + (j + 1) * lIndex] for j in lRange], dtype=float)
    yyyc = (yyyr + yyyl) / 2.0

    # calculate the kaxis block coordinates
    if zfaces is not None:
        lIndex, lRange = gr_lIndexSize[2], range(gr_axisNumProcs[2])
        zzzl = numpy.array([zfaces[0 + k * lIndex:0 + (k + 1) * lIndex] for k in lRange])
        zzzr = numpy.array([zfaces[1 + k * lIndex:1 + (k + 1) * lIndex] for k in lRange])
        zzzc = (zzzr + zzzl) / 2.0
    else:
        zzzl, zzzr, zzzc = None, None, None

    return (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr)

@safe
def get_grids(*, coords: Coords, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Grids:
    """Calculate block (by process mesh) coordinate arrays for each staggered grid from block coordinate face arrays."""

    # get the processor communicator layout, grid shapes, and block arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)
    gr_gridShapes = get_shapes(ndim=ndim, procs=procs, sizes=sizes)
    (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr) = get_faces(coords=coords, ndim=ndim, procs=procs, sizes=sizes)

    # create the staggered grid coordinate arrays
    grids = {grid: tuple(numpy.zeros((procs, size), dtype=float) if n < ndim else None 
        for n, (procs, size) in enumerate(zip(gr_axisNumProcs, shape[::-1]))) for grid, (procs, *shape) in gr_gridShapes.items()}

    # calculate the cell centered coordinates
    grids['center'][0][:,:] = xxxc[:,:] # type: ignore
    grids['center'][1][:,:] = yyyc[:,:] # type: ignore

    # calculate the iaxis staggered coordinates
    grids['facex'][0][:,0] = xxxl[:,0]  # type: ignore
    grids['facex'][0][:,1:] = xxxr[:,:] # type: ignore
    grids['facex'][1][:,:] = yyyc[:,:]  # type: ignore

    # calculate the jaxis staggered coordinates
    grids['facey'][0][:,:] = xxxc[:,:]  # type: ignore
    grids['facey'][1][:,0] = yyyl[:,0]  # type: ignore
    grids['facey'][1][:,1:] = yyyr[:,:] # type: ignore

    # calculate the kaxis staggered coordinates
    if ndim == 3:
        grids['center'][2][:,:] = zzzc[:,:] # type: ignore
        grids['facex'][2][:,:] = zzzc[:,:]  # type: ignore
        grids['facey'][2][:,:] = zzzc[:,:]  # type: ignore
        grids['facez'][0][:,:] = xxxc[:,:]  # type: ignore
        grids['facez'][1][:,:] = yyyc[:,:]  # type: ignore
        grids['facez'][2][:,0] = zzzl[:,0]  # type: ignore
        grids['facez'][2][:,1:] = zzzr[:,:] # type: ignore
    else:
        grids['facez'] = (None, None, None)

    return grids

@safe
def get_shapes(*, ndim: int, procs: tuple[int , int, int], sizes: tuple[int, int, int]) -> Shapes:
    """Determine shape of simulation data on the relavent grids (e.g., center or facex)."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(*sizes, gr_axisNumProcs)
   
    # create shape data as dictionary
    shapes = {'center': tuple([gr_axisNumProcs.prod()] + gr_lIndexSize[::-1].tolist())}
    shapes['facex'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 0, 1))) 
    shapes['facey'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 1, 0)))
    if ndim == 3:
        shapes['facez'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (1, 0, 0)))

    return shapes

@single
def read_coords(*, ndim: int, path: str) -> Coords:
    """Read global coordinate axis arrays from an hdf5 file."""
    coords: M = cast(M, [None, None, None])
    filename = path + '/' + NAME
    with h5py.File(filename, 'r') as h5file:
        for index, axis in enumerate(AXES[:ndim]):
            coords[index] = h5file[axis + LABEL][:]
    x, y, z = coords
    return x, y, z

@squash
def write_coords(*, coords: Coords, ndim: int, path: str) -> None:
    """Write global coordinate axis arrays to an hdf5 file."""
    filename = path + '/' + NAME
    with h5py.File(filename, 'w') as h5file:
        for axis, coord in zip(AXES[:ndim], coords[:ndim]):
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
