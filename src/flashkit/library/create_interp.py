"""Create an initial flow field (block) using interpolated simulation data."""

# type annotations
from __future__ import annotations
from typing import cast 

# standard libraries
import os

# internal libraries
from ..core.error import LibraryError
from ..core.parallel import Index, safe
from ..core.progress import Bar
from ..core.tools import first_true
from ..resources import CONFIG
from ..support.files import H5Manager
from ..support.grid import axisMesh, axisUniqueIndex, get_grids, get_shapes
from ..support.types import N, Coords, Grids, Shapes

# external libraries
import numpy
import h5py # type: ignore
from scipy.interpolate import interpn # type: ignore

# define public interface
__all__ = ['interp_blocks', ]

# define configuration constants (internal)
BNAME = CONFIG['create']['block']['name']
METHOD = CONFIG['create']['interp']['method']

@safe
def interp_blocks(*, basename: str, bndboxes: N, centers: N, dest: str, filename: str, flows: dict[str, tuple[str, str, str]],
                  gridname: str, grids: Grids, ndim: int, nofile: bool, path: str, procs: tuple[int, int, int],
                  shapes: Shapes, step: int, context: Bar) -> dict[str, N]:
    """Interpolate desired initial flow fields from a simulation output to another computional grid."""
    
    # define necessary filenames on the correct path
    lw_blk_name = os.path.join(path, basename + filename + f'{step:04}')
    lw_grd_name = os.path.join(path, basename + gridname + '0000')
    gr_blk_name = os.path.join(dest, BNAME)

    # create grid init parameters for parallelizing blocks 
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_numProcs = int(numpy.prod(gr_axisNumProcs))
    gr_lIndex = Index.from_simple(gr_numProcs)
    gr_lMesh = gr_lIndex.mesh_width(gr_axisNumProcs)

    # read simulation information from low resolution
    with h5py.File(lw_blk_name, 'r') as file:
        scalars = list(file['integer scalars'])
        runtime = list(file['integer runtime parameters'])
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
    if ndim != lw_ndim:
        raise LibraryError('Incompatible source and destination grids for interpolation!')

    # construct coord and shape dictionaries from low resolution
    with h5py.File(lw_grd_name, 'r') as file:
        faxes = (file[axis][()] for axis in ('xxxf', 'yyyf', 'zzzf'))
        uinds = axisUniqueIndex(*lw_axisNumProcs)
        coords = cast(Coords, tuple(numpy.append(a[i][:,:-1].flatten(), a[-1,-1]) if a is not None else None for a, i in zip(faxes, uinds)))
        lw_grids = get_grids(coords=coords, ndim=lw_ndim, procs=lw_axisNumProcs, sizes=lw_sizes)
        lw_shapes = get_shapes(ndim=lw_ndim, procs=lw_axisNumProcs, sizes=lw_sizes)
        del faxes, uinds, coords

    # open input and output files for performing the interpolation (writing the data as we go is most memory efficient)
    with H5Manager(lw_blk_name, 'r', force=True) as inp_file, \
            H5Manager(gr_blk_name, 'w-', clean=True, nofile=nofile) as out_file, \
            context(gr_lIndex.size) as progress:

        # create datasets in output file
        output = {}
        for field, (location, _, _) in flows.items():
            out_file.create_dataset(field, shape=shapes[location], dtype=float)
            output[field] = numpy.empty((gr_lIndex.size, ) + shapes[location][1:], numpy.double)
        
        # interpolate over assigned blocks
        for step, (block, mesh, bbox) in enumerate(zip(gr_lIndex.range, gr_lMesh, bndboxes[gr_lIndex.range])):

            # get blocks in the low grid that overlay the high grid
            lw_blocks = blocks_from_bbox(lw_bndboxes, bbox)
            progress.text(f'from {lw_blocks}')

            # gather necessary information to flatten source data from low grid
            lw_unq_center = [numpy.unique(lw_centers[:, axis]) for axis in range(3)]
            lw_flt_center = [numpy.unique(lw_centers[lw_blocks, axis]) for axis in range(3)]
            lw_flt_extent = [len(axis) for axis in lw_flt_center]
            lw_flt_bindex = [[numpy.where(lw_flt_center[axis] == coord)[0][0] 
                for axis, coord in enumerate(block)] for block in lw_centers[lw_blocks]]
            lw_flt_uindex = [numpy.unique([numpy.where(lw_unq_center[axis] == coord[axis])[0][0] 
                for coord in lw_centers[lw_blocks]]) for axis in range(3)]

            # interpolate each field for the working block
            for field, (gr_loc, lw_fld, lw_loc) in flows.items():

                # calculate flattened source data shape on low grid
                #   -- cannot use interpn w/ repeats; all grids cnt shaped
                xslice = slice(None, -1 if lw_loc == 'facex' else None)
                yslice = slice(None, -1 if lw_loc == 'facey' else None)
                zslice = slice(None, -1 if lw_loc == 'facez' else None)
                lw_blk_fshape = lw_shapes[lw_loc][:0:-1]
                lw_flt_fshape = [extent * size for extent, size in zip(lw_flt_extent, lw_sizes)]

                if lw_ndim == 3:
                
                    # interpolate cell center fields
                    xxx = lw_grids[lw_loc][0][lw_flt_uindex[0]][:,xslice].flatten() # type: ignore
                    yyy = lw_grids[lw_loc][1][lw_flt_uindex[1]][:,yslice].flatten() # type: ignore
                    zzz = lw_grids[lw_loc][2][lw_flt_uindex[2]][:,zslice].flatten() # type: ignore
                    values = numpy.empty(lw_flt_fshape[::-1], dtype=float)
                    for (i, j, k), source in zip(lw_flt_bindex, lw_blocks):
                        il, ih = i * lw_sizes[0], (i + 1) * lw_sizes[0]
                        jl, jh = j * lw_sizes[1], (j + 1) * lw_sizes[1]
                        kl, kh = k * lw_sizes[2], (k + 1) * lw_sizes[2]
                        values[kl:kh, jl:jh, il:ih] = inp_file.read(lw_fld)[source, zslice, yslice, xslice]

                    x = grids[gr_loc][0][mesh[0], None, None, :] # type: ignore
                    y = grids[gr_loc][1][mesh[1], None, :, None] # type: ignore
                    z = grids[gr_loc][2][mesh[2], :, None, None] # type: ignore
                
                    output[field][step] = numpy.maximum(numpy.minimum(
                        interpn((zzz, yyy, xxx), values, (z, y, x), method=METHOD, bounds_error=False, fill_value=None),
                        values.max()), values.min())
                    out_file.write_partial(field, output[field][step], block=block, index=gr_lIndex) 

                elif lw_ndim == 2:
                    
                    # interpolate cell center fields
                    xxx = lw_grids[lw_loc][0][lw_flt_uindex[0]][:,xslice].flatten() # type: ignore
                    yyy = lw_grids[lw_loc][1][lw_flt_uindex[1]][:,yslice].flatten() # type: ignore
                    values = numpy.empty(lw_flt_fshape[1::-1], dtype=float)
                    for (i, j, _), source in zip(lw_flt_bindex, lw_blocks):
                        il, ih = i * lw_sizes[0], (i + 1) * lw_sizes[0]
                        jl, jh = j * lw_sizes[1], (j + 1) * lw_sizes[1]
                        values[jl:jh, il:ih] = inp_file.read(lw_fld)[source, 0, yslice, xslice]

                    x = grids[gr_loc][0][mesh[0], None, :] # type: ignore
                    y = grids[gr_loc][1][mesh[1], :, None] # type: ignore
                
                    output[field][step] = numpy.maximum(numpy.minimum(
                        interpn((yyy, xxx), values, (y, x), method=METHOD, bounds_error=False, fill_value=None),
                        values.max()), values.min())[None, :, :]
                    out_file.write_partial(field, output[field][step], block=block, index=gr_lIndex) 

                else:
                    pass

            progress()
            
    return output

def blocks_from_bbox(boxes, box):
    """Return all boxes that at least partially overlap box."""
    overlaps = lambda ll, lh, hl, hh : not ((hh < ll) or (hl > lh))
    return [blk for blk, bb in enumerate(boxes)
            if all(overlaps(*low, *high) for low, high in zip(bb, box))]
