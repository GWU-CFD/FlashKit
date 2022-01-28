"""Create an initial simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import Any, cast

# standard libraries
import os

# internal libraries
from ..core import parallel
from ..resources import CONFIG 
from ..support.grid import axisMesh
from ..support.files import H5Manager
from ..support.flow import Flowing
from ..support.types import N, Blocks, Grids, Mesh, Shapes 

# external libraries
import numpy

# define public interface
__all__ = ['calc_blocks', 'write_blocks', ]

# define configuration constants (internal)
NAME = CONFIG['create']['block']['name']

@parallel.safe
def calc_blocks(*, flows: dict[str, tuple[str, str]], grids: Grids, params: dict[str, Any], 
                path: str, procs: tuple[int, int, int], shapes: Shapes) -> tuple[Blocks, parallel.Index]:
    """Calculate desired initial flow fields; dispatches appropriate method using local blocks."""

    # create grid init parameters for parallelizing blocks 
    gr_axisNumProcs, _ = axisMesh(*procs)
    gr_numProcs = int(numpy.prod(gr_axisNumProcs))
    gr_lIndex = parallel.Index.from_simple(taskes=gr_numProcs, layout=gr_axisNumProcs)
    gr_lMesh = gr_lIndex.mesh_width(gr_axisNumProcs)

    # create flow field method from parameters
    gr_shp = {grid: (len(gr_lMesh), ) + tuple(shape) for grid, (_, *shape) in shapes.items()}
    gr_loc = {field: location for field, (location, _) in flows.items()}
    gr_mth = {field: method for field, (_, method) in flows.items()}
    gr_flw = Flowing(gr_mth, path, **params)

    # create flow fields
    return get_filledBlocks(grids=grids, locations=gr_loc, mesh=gr_lMesh, methods=gr_flw, shapes=gr_shp), gr_lIndex

@parallel.safe
def write_blocks(*, blocks: Blocks, index: parallel.Index, path: str, shapes: Shapes) -> None:
    filename = os.path.join(path, NAME)
    with H5Manager(filename, 'w-', clean=True) as h5file:
        for field, data in blocks.items():
            shape = (shapes['center'][0], ) + data.shape[1:] 
            h5file.write(field, data, index=index, shape=shape)

def get_filledBlocks(*, grids: Grids, locations: dict[str, str], mesh: Mesh, methods: Flowing, shapes: Shapes) -> Blocks:
    blocks: Blocks = cast(Blocks, {field: None for field in locations.keys()})
    for method, func in methods.flow.items():
        if methods.any_fields(method):
            fields = {field: locations[field] for field in methods.map_fields(method)}
            func(blocks=blocks, fields=fields, grids=grids, mesh=mesh, shapes=shapes)
    return blocks
