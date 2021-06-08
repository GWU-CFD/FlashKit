"""Support methods provided for the grid (e.g., sizing, arrangment, shape, and bbox algorithms)."""

# type annotations
from __future__ import annotations

# internal libraries
from .types import N, Coords, Faces, Grids, Shapes

# external libraries
import numpy

# define public interface
__all__ = ['axisMesh', 'axisUniqueIndex', 'get_blocks', 'get_faces', 'get_grids', 'get_shapes', 
           'indexSize_fromGlobal', 'indexSize_fromLocal', ]

def axisMesh(iProcs: int, jProcs: int, kProcs: int) -> tuple[N, N]:
    """Create a simple grid of processes along the axes and return the mesh."""
    proc = numpy.array([iProcs, jProcs, kProcs], int)
    grid = numpy.array([[i, j, k] for k in range(kProcs) for j in range(jProcs) for i in range(iProcs)], int)
    return proc, grid

def axisUniqueIndex(iProcs: int, jProcs: int, kProcs: int) -> tuple[N, N, N]:
    """Create a grid of the unique (i.e., first) indicies and associated processes along each axis."""
    _, gr_axisMesh = axisMesh(iProcs, jProcs, kProcs)
    iInd = numpy.array([n for n in range(iProcs)])
    jInd = numpy.array([n for n, (i, j, k) in enumerate(gr_axisMesh) if i == 0])
    kInd = numpy.array([n for n, (i, j, k) in enumerate(gr_axisMesh) if i == 0 and j == 0])
    return iInd, jInd, kInd

def get_blocks(*, coords: Coords, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> tuple[N, N]:
    """Calculate block (center) coordinates and bounding boxes from face arrays."""

    # get the processor communicator layout, grid shapes, and block arrays
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_lIndexSize, gr_gIndexSize = indexSize_fromLocal(*sizes, gr_axisNumProcs)
    gr_gridShapes = get_shapes(ndim=ndim, procs=procs, sizes=sizes)
    (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr) = get_faces(coords=coords, ndim=ndim, procs=procs, sizes=sizes)

    # create bounding boxes for each block
    bboxes = numpy.array([((xxxl[i,0], xxxr[i,-1]), (yyyl[j,0], yyyr[j,-1]), (0, 0) if ndim < 3 else (zzzl[k,0], zzzr[k,-1]))
        for i, j, k in gr_axisMesh], float)
    
    # create block centers from bboxes
    centers = numpy.array([[sum(axis) / 2 for axis in box] for box in bboxes], float)
    return centers, bboxes

def get_faces(*, coords: Coords, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Faces:
    """Calculate block (unique axis mesh) coordinate arrays from global axis arrays for each face."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_lIndexSize, gr_gIndexSize = indexSize_fromLocal(*sizes, gr_axisNumProcs)
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

def get_grids(*, coords: Coords, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Grids:
    """Calculate block (unique axis mesh) coordinate arrays for each staggered grid from face arrays."""

    # get the processor communicator layout, grid shapes, and block arrays
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_lIndexSize, gr_gIndexSize = indexSize_fromLocal(*sizes, gr_axisNumProcs)
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

def get_shapes(*, ndim: int, procs: tuple[int , int, int], sizes: tuple[int, int, int]) -> Shapes:
    """Determine shape of simulation data on the relavent grids (e.g., center or facex)."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_lIndexSize, gr_gIndexSize = indexSize_fromLocal(*sizes, gr_axisNumProcs)
   
    # create shape data as dictionary
    shapes = {'center': tuple([gr_axisNumProcs.prod()] + gr_lIndexSize[::-1].tolist())}
    shapes['facex'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 0, 1))) 
    shapes['facey'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 1, 0)))
    if ndim == 3:
        shapes['facez'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (1, 0, 0)))

    return shapes

def indexSize_fromGlobal(i: int, j: int, k: int, ijkProcs: N) -> tuple[N, N]:
    gSizes = numpy.array([i, j, k], int)
    blocks = numpy.array([size / procs for procs, size in zip(ijkProcs, gSizes)], int)
    return blocks, gSizes

def indexSize_fromLocal(i: int, j: int, k: int, ijkProcs: N) -> tuple[N, N]:
    blocks = numpy.array([i, j, k], int)
    gSizes = numpy.array([procs * nb for procs, nb in zip(ijkProcs, blocks)], int)
    return blocks, gSizes

