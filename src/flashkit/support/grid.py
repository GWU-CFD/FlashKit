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
    jInd = numpy.array([n for n, (i, _, k) in enumerate(gr_axisMesh) if i == 0 and k == 0])
    kInd = numpy.array([n for n, (i, j, _) in enumerate(gr_axisMesh) if i == 0 and j == 0])
    return iInd, jInd, kInd

def get_blocks(*, coords: Coords, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> tuple[N, N]:
    """Calculate block (center) coordinates and bounding boxes from face arrays."""

    # get the processor communicator layout, grid shapes, and block arrays
    _, gr_axisMesh = axisMesh(*procs)
    (xxxl, _, xxxr), (yyyl, _, yyyr), (zzzl, _, zzzr) = get_faces(coords=coords, procs=procs, sizes=sizes)

    # create bounding boxes for each block
    bboxes = numpy.array([((xxxl[i,0], xxxr[i,-1]), (yyyl[j,0], yyyr[j,-1]), (0, 0) if ndim < 3 else (zzzl[k,0], zzzr[k,-1]))
        for i, j, k in gr_axisMesh], float)
    
    # create block centers from bboxes
    centers = numpy.array([[sum(axis) / 2 for axis in box] for box in bboxes], float)
    return centers, bboxes

def get_faces(*, coords: Coords, guard: bool = False, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Faces:
    """Calculate block (unique axis mesh) coordinate arrays; with or without guard cells filled in."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, _ = axisMesh(*procs)
    gr_lIndexSize, _   = indexSize_fromLocal(*sizes, gr_axisNumProcs, False)
    gr_lIndexSizeGC, _ = indexSize_fromLocal(*sizes, gr_axisNumProcs, True)
    xfaces, yfaces, zfaces = coords
    ndim = 3 if zfaces is not None else 2

    # calculate the global coordinates on each face
    xglb = numpy.array([xfaces[:-1], (xfaces[1:] + xfaces[:-1]) / 2.0, xfaces[1:]], dtype=float)
    yglb = numpy.array([yfaces[:-1], (yfaces[1:] + yfaces[:-1]) / 2.0, yfaces[1:]], dtype=float)
    if ndim == 3:
        zglb = numpy.array([zfaces[:-1], (zfaces[1:] + zfaces[:-1]) / 2.0, zfaces[1:]], dtype=float)
    else:
        zglb = [None, None, None]

    # reserve memory for the block coordinates on each face
    xblk = numpy.empty((3, gr_axisNumProcs[0], gr_lIndexSizeGC[0]), dtype=float)
    yblk = numpy.empty((3, gr_axisNumProcs[1], gr_lIndexSizeGC[1]), dtype=float)
    if ndim == 3:
        zblk = numpy.empty((3, gr_axisNumProcs[2], gr_lIndexSizeGC[2]), dtype=float)
    else:
        zblk = [None, None, None]

    # calculate each axis block coordinates for each face
    for axis, (wglb, wblk, procs, size) in enumerate(zip((xglb, yglb, zglb), (xblk, yblk, zblk), gr_axisNumProcs, gr_lIndexSize)):

        # skip zblk if 2d
        if axis == ndim:
            break

        # handle each block and type
        for block in range(procs):

            if procs == 1: # single interior block

                low = block * size
                high = (block + 1) * size
                wblk[:,block,1:-1] = wglb[:,low:high]
                wblk[:,block,0] = wglb[:,1] + 2 * (wglb[:,1] - wglb[:,2])
                wblk[:,block,-1] = wglb[:,-2] + 2 * (wglb[:,-2] - wglb[:,-3])
            
            elif block == 0: # left edge block
                
                low = block * size
                high = (block + 1) * size + 1
                wblk[:,block,1:] = wglb[:,low:high]
                wblk[:,block,0] = wglb[:,1] + 2 * (wglb[:,1] - wglb[:,2])

            elif block == procs - 1: # right edge block

                low = block * size - 1
                high = (block + 1) * size
                wblk[:,block,:-1] = wglb[:,low:high]
                wblk[:,block,-1] = wglb[:,-2] + 2 * (wglb[:,-2] - wglb[:,-3])

            else: # interior block

                low = block * size - 1
                high = (block + 1) * size + 1
                wblk[:,block,:] = wglb[:,low:high]

    # handle whether or not guards requested
    sliced = slice(1,-1) if not guard else slice(None,None)
    xxxl, xxxc, xxxr = xblk[:,:,sliced]
    yyyl, yyyc, yyyr = yblk[:,:,sliced]
    if ndim == 3:
        zzzl, zzzc, zzzr = zblk[:,:,sliced]
    else:
        zzzl, zzzc, zzzr = zblk

    return (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr)

def get_grids(*, coords: Coords, guard: bool = False, ndim: int, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Grids:
    """Calculate block (unique axis mesh) coordinate arrays for each staggered grid from face arrays."""

    # get the processor communicator layout, grid shapes, and block arrays
    gr_axisNumProcs, _ = axisMesh(*procs)
    gr_gridShapes = get_shapes(guard=guard, ndim=ndim, procs=procs, sizes=sizes)
    (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr) = get_faces(coords=coords, guard=guard, procs=procs, sizes=sizes)

    # create the staggered grid coordinate arrays
    grids = {grid: tuple(numpy.zeros((procs, size), dtype=float) if n < ndim else None 
        for n, (procs, size) in enumerate(zip(gr_axisNumProcs, shape[::-1]))) for grid, (_, *shape) in gr_gridShapes.items()}

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

def get_metrics(*, coords: Coords, guard: bool = False, procs: tuple[int, int, int], sizes: tuple[int, int, int]) -> Faces:
    """Calculate block (unique axis mesh) metric arrays; with or without guard cells filled in."""

    # get the processor communicator layout, grid shapes, and block arrays
    gr_axisNumProcs, _ = axisMesh(*procs)
    gr_lIndexSizeGC, _ = indexSize_fromLocal(*sizes, gr_axisNumProcs, True)
    xfaces, yfaces, zfaces = get_faces(coords=coords, guard=True, procs=procs, sizes=sizes)
    ndim = 3 if coords[2] is not None else 2

    # convert face tuples to numpy arrays
    xblk = numpy.array(xfaces, dtype=float)
    yblk = numpy.array(yfaces, dtype=float)
    if ndim == 3:
        zblk = numpy.array(zfaces, dtype=float)
    else:
        zblk = [None, None, None]

    # reserve memory for the block metrics on each face
    ddxblk = numpy.empty((3, gr_axisNumProcs[0], gr_lIndexSizeGC[0]), dtype=float)
    ddyblk = numpy.empty((3, gr_axisNumProcs[1], gr_lIndexSizeGC[1]), dtype=float)
    if ndim == 3:
        ddzblk = numpy.empty((3, gr_axisNumProcs[2], gr_lIndexSizeGC[2]), dtype=float)
    else:
        ddzblk = [None, None, None]

    # handle each axis block metrics for each face 
    for axis, (ddwblk, wblk) in enumerate(zip((ddxblk, ddyblk, ddzblk), (xblk, yblk, zblk))):

        # skip ddzblk if 2d
        if axis == ndim:
            break

        # definitions of metric coefficients
        ddwblk[1,:,:]   = 1.0 / (wblk[2,:,:]  - wblk[0,:,:])
        ddwblk[2,:,:-1] = 1.0 / (wblk[1,:,1:] - wblk[1,:,:-1])
        ddwblk[2,:,-1]  = 2.0 / ( 3.0 * wblk[2,:,-1] - 4.0 * wblk[2,:,-2] + wblk[2,:,-3])
        ddwblk[0,:,1:]  = 1.0 / (wblk[1,:,1:] - wblk[1,:,:-1])
        ddwblk[0,:,0]   = 2.0 / (-3.0 * wblk[0,:,0]  + 4.0 * wblk[0,:,1]  - wblk[0,:,2])

    # handle whether or not guards requested
    sliced = slice(1,-1) if not guard else slice(None,None)
    ddxl, ddxc, ddxr = ddxblk[:,:,sliced]
    ddyl, ddyc, ddyr = ddyblk[:,:,sliced]
    if ndim == 3:
        ddzl, ddzc, ddzr = ddzblk[:,:,sliced]
    else:
        ddzl, ddzc, ddzr = ddzblk

    return (ddxl, ddxc, ddxr), (ddyl, ddyc, ddyr), (ddzl, ddzc, ddzr)

def get_shapes(*, guard: bool = False, ndim: int, procs: tuple[int , int, int], sizes: tuple[int, int, int]) -> Shapes:
    """Determine shape of simulation data on the relavent grids (e.g., center or facex)."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, _ = axisMesh(*procs)
    gr_lIndexSize, _ = indexSize_fromLocal(*sizes, gr_axisNumProcs, guard)
   
    # create shape data as dictionary
    shapes = {'center': tuple([gr_axisNumProcs.prod()] + gr_lIndexSize[::-1].tolist())}
    shapes['facex'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 0, 1))) 
    shapes['facey'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 1, 0)))
    if ndim == 3:
        shapes['facez'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (1, 0, 0)))

    return shapes

def indexSize_fromGlobal(i: int, j: int, k: int, ijkProcs: N, guard: bool = False) -> tuple[N, N]:
    """Provide both the number of cells in a block and in the domain; based on global domain variables."""
    gc = 0 if not guard else 2
    gSizes = numpy.array([i, j, k], int)
    blocks = numpy.array([size / procs + gc for procs, size in zip(ijkProcs, gSizes)], int)
    return blocks, gSizes

def indexSize_fromLocal(i: int, j: int, k: int, ijkProcs: N, guard: bool = False) -> tuple[N, N]:
    """Provide both the number of cells in a block and in the domain; based on local block variables."""
    gc = 0 if not guard else 2
    gSizes = numpy.array([procs * nb for procs, nb in zip(ijkProcs, [i, j, k])], int)
    blocks = numpy.array([i + gc, j + gc, k + gc], int)
    return blocks, gSizes