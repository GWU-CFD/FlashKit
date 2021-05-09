"""Create an initial flow field (block) using interpolated simulation data."""

# type annotations
from __future__ import annotations
from typing import cast, Tuple

# standard libraries
import os

# internal libraries
from ..core import parallel
from ..core.error import LibraryError
from ..core.logging import printer
from ..core.progress import Bar
from ..core.tools import first_true
from ..resources import CONFIG
from ..support.grid import axisMesh, axisUniqueIndex, get_grids, get_shapes
from ..support.types import N, Grids, Shapes

# external libraries
import numpy
import h5py # type: ignore
from scipy.interpolate import interpn # type: ignore

# define public interface
__all__ = ['interp_blocks', ]

# define configuration constants (internal)
BNAME = CONFIG['create']['block']['name']
AXES = CONFIG['create']['grid']['coords']
LABEL = CONFIG['create']['grid']['label']
METHOD = CONFIG['create']['interp']['method']

@parallel.safe
def interp_blocks(*, basename: str, bndboxes: N, centers: N, dest: str, filename: str, flows: dict[str, str],
                  gridname: str, grids: Grids, ndim: int, procs: tuple[int, int, int], shapes: Shapes, 
                  source: str, step: int, context: Bar) -> None:
    """Interpolate desired initial flow fields from a simulation output to another computional grid."""
    
    # define necessary filenames on the correct path
    lw_blk_name = os.path.join(source, basename + filename + f'{step:04}')
    lw_grd_name = os.path.join(source, basename + gridname + '0000')
    gr_blk_name = os.path.join(os.path.relpath(source, dest), BNAME)

    # create grid init parameters for parallelizing blocks 
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_numProcs = int(numpy.prod(gr_axisNumProcs))
    gr_lIndex = parallel.Index.from_simple(gr_numProcs)
    gr_lMesh = gr_lIndex.mesh_width(gr_axisNumProcs)

    # read simulation information from low resolution
    with h5py.File(lw_blk_name, 'r') as file:
        scalars = list(file['integer scalars'])
        runtime = list(file['integer runtime scalars'])
        lw_numProcs = first_true(scalars, lambda l: 'globalnumblocks' in str(l[0]))[1]
        lw_axisNumProcs = (
                first_true(runtime, lambda l: 'iprocs' in str(l[0]))[1],
                first_true(runtime, lambda l: 'jprocs' in str(l[0]))[1],
                first_true(runtime, lambda l: 'kprocs' in str(l[0]))[1])
        lw_sizes = (
                first_true(scalars, lambda l: 'nxb' in str(l[0]))[1],
                first_true(scalars, lambda l: 'nyb' in str(l[0]))[1],
                first_true(scalars, lambda l: 'nzb' in str(l[0]))[1])
        lw_bndboxes = file['bounding box'][()]    
        lw_centers = file['coordinates'][()]
        lw_ndim = first_true(scalars, lambda l: 'dimensionality' in str(l[0]))[1]
        del scalars, runtime

    # check that source and destination are compatible
    try:
        assert(ndim == lw_ndim)
    except AssertionError as error:
        raise LibraryError('Incompatible source and destination grids for interpolation!') from error

    # construct coord and shape dictionaries from low resolution
    with h5py.File(lw_grd_name, 'r') as file:
        faxes = (file[axis][()] for axis in ('xxxf', 'yyyf', 'zzzf'))
        uinds = axisUniqueIndex(*lw_axisNumProcs)
        coords = cast(Tuple[N, N, N], tuple(numpy.append(a[i][:,:-1].flatten(), a[-1,-1]) if a is not None else None for a, i in zip(faxes, uinds)))
        lw_grids = get_grids(coords=coords, ndim=lw_ndim, procs=lw_axisNumProcs, sizes=lw_sizes)
        lw_shapes = get_shapes(ndim=lw_ndim, procs=lw_axisNumProcs, sizes=lw_sizes)
        del faxes, uinds, coords

    # open input and output files for performing the interpolation (writing the data as we go is most memory efficient)
    with h5py.File(lw_blk_name, 'r') as inp_file, h5py.File(gr_blk_name, 'w', driver='mpio', comm=parallel.COMM_WORLD) as out_file:

        # create datasets in output file
        dsets = {field: out_file.create_dataset(field, shapes[location], dtype=float) for field, location in flows.items()}

        # interpolate over assigned blocks
        for step, (block, mesh, bbox) in enumerate(zip(gr_lIndex.range, gr_lMesh, bndboxes[gr_lIndex.range])):

            # get blocks in the low grid that overlay the high grid
            blocks = blocks_from_bbox(lw_bndboxes, bbox)

            # gather necessary information to flatten source data from low grid
            lw_flt_center = [numpy.unique(lw_centers[blocks, axis]) for axis in range(3)]
            lw_flt_extent = [len(axis) for axis in lw_flt_center]
            lw_flt_bindex = [[numpy.where(lw_flt_center[axis] == coord)[0][0]
                               for axis, coord in enumerate(block)] for block in lw_centers[blocks]]
            lw_flt_fshape = [extent * size for extent, size in zip(lw_flt_extent, lw_shapes['center'])]

            if lw_ndim == 3:
                pass

            elif lw_ndim == 2:

                # interpolate cell center fields
                xxx = lw_grids['center'][lw_flt_bindex[:, 0]].flatten() # type: ignore
                yyy = lw_grids['center'][lw_flt_bindex[:, 1]].flatten() # type: ignore
                values = numpy.empty(lw_flt_fshape, dtype=float)
                for (i, j, _), source in zip(lw_flt_bindex, blocks):
                    il, ih = i * lw_sizes[0], (i + 1) * lw_sizes
                    jl, jh = j * lw_sizes[1], (j + 1) * lw_sizes
                    values[jl:jh, il:ih] = inp_file['temp'][source, 0, :, :]

                x = grids['center'][mesh[0], None, :] # type: ignore
                y = grids['center'][mesh[1], :, None] # type: ignore

                dsets['temp'][block, 0, :, :] = numpy.maximum(numpy.minimum(
                    interpn((yyy, xxx), values, (y, x), method=METHOD, bounds_error=False, fill_value=None),
                    values.max()), values.min())

            else:
                pass

def blocks_from_bbox(boxes, box):
    overlaps = lambda ll, lh, hl, hh : not ((hh < ll) or (hl > lh))
    return [blk for blk, bb in enumerate(boxes)
            if all(overlaps(*low, *high) for low, high in zip(bb, box))]
