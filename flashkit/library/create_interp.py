"""Create an initial flow field (block) using interpolated simulation data."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

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
GNAME = CONFIG['create']['grid']['name']
AXES = CONFIG['create']['grid']['coords']
LABEL = CONFIG['create']['grid']['label']
METHOD = CONFIG['create']['interp']['method']

@parallel.safe
def interp_blocks(*, basename: str, bndboxes: N, centers: N, dest: str, filename: str, flows: dict[str, str],
                  gridname: str, grids: Grids, ndim: int, procs: tuple[int, int, int], shapes: Shapes, 
                  sizes: tuple[int, int, int], source: str, step: int, context: Bar) -> None:
    """Interpolate desired initial flow fields from a simulation output to another computional grid."""
    
    # define necessary filenames on the correct path
    low_blk_name = os.path.join(source, basename + filename + f'{step:04}')
    low_grd_name = os.path.join(source, basename + gridname + '0000')
    high_blk_name = os.path.join(os.path.relpath(source, dest), BNAME)
    high_grd_name = os.path.join(os.path.relpath(source, dest), GNAME)

    # create grid init parameters for parallelizing blocks 
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_numProcs = int(numpy.prod(gr_axisNumProcs))
    gr_lIndex = parallel.Index.from_simple(gr_numProcs)
    gr_lMesh = gr_lIndex.mesh_width(gr_axisNumProcs)

    # simulation information for high resolution
    high_blk_num = gr_numProcs
    high_blk_bndbox = bndboxes
    high_grd_dim = ndim
    high_grd_coords = grids
    high_grd_shapes = shapes

    # read simulation information from low resolution
    with h5py.File(low_blk_name, 'r') as file:
        scalars = list(file['integer scalars'])
        runtime = list(file['integer runtime scalars'])
        low_blk_num = first_true(scalars, lambda l: 'globalnumblocks' in str(l[0]))[1]
        low_blk_num_x = first_true(runtime, lambda l: 'iprocs' in str(l[0]))[1]
        low_blk_num_y = first_true(runtime, lambda l: 'jprocs' in str(l[0]))[1]
        low_blk_num_z = first_true(runtime, lambda l: 'kprocs' in str(l[0]))[1]
        low_blk_size_x = first_true(scalars, lambda l: 'nxb' in str(l[0]))[1]
        low_blk_size_y = first_true(scalars, lambda l: 'nyb' in str(l[0]))[1]
        low_blk_size_z = first_true(scalars, lambda l: 'nzb' in str(l[0]))[1]
        low_blk_bndbox = file['bounding box'][()]    
        low_blk_center = file['coordinates'][()]
        low_grd_dim = first_true(scalars, lambda l: 'dimensionality' in str(l[0]))[1]
        del scalars, runtime

    # check that source and destination are compatible
    try:
        assert(high_grd_dim == low_grd_dim)
    except AssertionError as error:
        raise LibraryError('Incompatible source and destination grids for interpolation!') from error

    # construct coord and shape dictionaries from low resolution
    with h5py.File(low_grd_name, 'r') as file:
        xxxf, yyyf, zzzf = (file[axis][()] for axis in ('xxxf', 'yyyf', 'zzzf'))
        xind, yind, zind = axisUniqueIndex(low_blk_num_x, low_blk_num_y, low_blk_num_z)
        low_grd_coords = get_grids(coords=(xxxf[xind], yyyf[yind], zzzf[zind]), ndim=low_grd_dim,
                                   procs=(low_blk_num_x, low_blk_num_y, low_blk_num_z),
                                   sizes=(low_blk_size_x, low_blk_size_y, low_blk_size_z))
        low_grd_shapes = get_shapes(ndim=low_grd_dim,
                                    procs=(low_blk_num_x, low_blk_num_y, low_blk_num_z),
                                    sizes=(low_blk_size_x, low_blk_size_y, low_blk_size_z))
        del xxxf, yyyf, zzzf, xind, yind, zind

    # open input and output files for performing the interpolation (writing the data as we go is most memory efficient)
    with h5py.File(low_blk_name, 'r') as inp_file, h5py.File(high_blk_name, 'w', driver='mpio', comm=parallel.COMM_WORLD) as out_file:

        # create datasets in output file
        dsets = {field: out_file.create_dataset(field, high_grd_shapes[location], dtype=float) for field, location in flows.items()}

        # interpolate over assigned blocks
        for step, (block, mesh, bbox) in enumerate(zip(gr_lIndex.range, gr_lMesh, high_blk_bndbox[gr_lIndex.range])):

            # get blocks in the low grid that overlay the high grid
            blocks = blocks_from_bbox(low_blk_bndbox, bbox)

            # gather necessary information to flatten source data from low grid
            low_flt_center = [numpy.unique(low_blk_center[blocks, axis]) for axis in range(3)]
            low_flt_extent = [len(axis) for axis in low_flt_center]
            low_flt_bindex = [[numpy.where(low_flt_center[axis] == coord)[0][0]
                               for axis, coord in enumerate(block)] for block in low_blk_center[blocks]]
            low_flt_fshape = [extent * size for extent, size in zip(low_flt_extent, low_grd_shapes['center'])]

            if low_grd_dim == 3:
                pass

            elif low_grd_dim == 2:

                # interpolate cell center fields
                xxx = low_grd_coords['center'][low_flt_bindex[:, 0]].flatten() # type: ignore
                yyy = low_grd_coords['center'][low_flt_bindex[:, 1]].flatten() # type: ignore
                values = numpy.empty(low_flt_fshape[1::-1], dtype=float)
                for (i, j, k), source in zip(low_flt_bindex, blocks):
                    il, ih = i * low_blk_size_x, (i + 1) * low_blk_size_x
                    jl, jh = j * low_blk_size_y, (j + 1) * low_blk_size_y
                    kl, kh = k * low_blk_size_z, (k + 1) * low_blk_size_z
                    values[kl:kh, jl:jh, il:ih] = inp_file['temp'][source, :, :, :]

                x = high_grd_coords['center'][mesh[0], None, :] # type: ignore
                y = high_grd_coords['center'][mesh[1], :, None] # type: ignore

                dsets['temp'][block, 0, :, :] = numpy.maximum(numpy.minimum(
                    interpn((yyy, xxx), values, (y, x), method=METHOD, bounds_error=False, fill_value=None),
                    values.max()), values.min())

            else:
                pass

def blocks_from_bbox(boxes, box):
    overlaps = lambda ll, lh, hl, hh : not ((hh < ll) or (hl > lh))
    return [blk for blk, bb in enumerate(boxes)
            if all(overlaps(*low, *high) for low, high in zip(bb, box))]
