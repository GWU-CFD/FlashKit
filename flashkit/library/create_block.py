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
from ..support.flow import Flowing
from ..support.types import N, Blocks, Grids, Mesh, Shapes 

# external libraries
import numpy
import h5py # type: ignore

# define public interface
__all__ = ['calc_blocks', 'write_blocks', ]

# define configuration constants (internal)
NAME = CONFIG['create']['block']['name']

@parallel.safe
def calc_blocks(*, flows: dict[str, tuple[str, str]], grids: Grids, params: dict[str, Any], 
                path: str, procs: tuple[int, int, int], shapes: Shapes) -> tuple[Blocks, parallel.Index]:
    """Calculate desired initial flow fields; dispatches appropriate method using local blocks."""

    # create grid init parameters for parallelizing blocks 
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_numProcs = int(numpy.prod(gr_axisNumProcs))
    gr_lIndex = parallel.Index.from_simple(gr_numProcs)
    gr_lMesh = gr_lIndex.mesh_width(gr_axisNumProcs)

    # create flow field method from parameters
    gr_shp = {grid: (len(gr_lMesh), ) + tuple(shape) for grid, (procs, *shape) in shapes.items()}
    gr_loc = {field: location for field, (location, _) in flows.items()}
    gr_mth = {field: method for field, (_, method) in flows.items()}
    gr_flw = Flowing(gr_mth, path, **params)

    # create flow fields
    return get_filledBlocks(grids=grids, locations=gr_loc, mesh=gr_lMesh, methods=gr_flw, shapes=gr_shp), gr_lIndex

@parallel.safe
def write_blocks(*, blocks: Blocks, index: parallel.Index, path: str, shapes: Shapes) -> None:
    
    # specify filename and remove if exists
    filename = os.path.join(path, NAME)
    if parallel.is_root() and os.path.exists(filename): 
        os.remove(filename)

    # write hdf5 file serially
    if parallel.is_serial():
        with h5py.File(filename, 'w-') as h5file:
            for field, data in blocks.items():
                h5file.create_dataset(field, data=data)
        return
    
    comm = parallel.COMM_WORLD
       
    # write hdf5 file with parallel support
    if 'mpio' in h5py.registered_drivers():
        with h5py.File(filename, 'w-', driver='mpio', comm=comm) as h5file:
            for field, data in blocks.items():
                shape = (shapes['center'][0], ) + data.shape[1:] 
                dset = h5file.create_dataset(field, shape, dtype=data.dtype)
                dset[index.low:index.high+1] = data
        return
        
    # write hdf5 file without parallel support
    if parallel.is_root():
        h5file = h5py.File('parallel.h5', 'w-')
        
    for field, data in blocks.items():
        shape = (shapes['center'][0], ) + data.shape[1:] 
            
        if parallel.is_root():
            dset = h5file.create_dataset(field, shape, dtype=data.dtype)
            
        for process in range(index.size):
            low, high = 0, 0

            if process == parallel.rank and parallel.is_root():
                dset[index.low:index.high+1] = data
                
            if process == parallel.rank and not parallel.is_root():
                comm.Send(data, dest=parallel.ROOT, tag=process)
                comm.Send((index.low, index.high), dest=parallel.ROOT, tag=process+index.size)
                
            if process != parallel.rank and parallel.is_root():
                comm.Recv(data, source=process, tag=process)
                comm.Recv((low, high), source=process, tag=process+index.size)
                dset[low:high+1] = data
        
    if parallel.is_root():
        h5file.close()

def get_filledBlocks(*, grids: Grids, locations: dict[str, str], mesh: Mesh, methods: Flowing, shapes: Shapes) -> Blocks:
    blocks: Blocks = cast(Blocks, {field: None for field in locations.keys()})
    for method, func in methods.flow.items():
        if methods.any_fields(method):
            fields = {field: locations[field] for field in methods.map_fields(method)}
            func(blocks=blocks, fields=fields, grids=grids, mesh=mesh, shapes=shapes)
    return blocks

