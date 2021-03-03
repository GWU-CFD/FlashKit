"""Create an initial simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os

# internal libraries
from .create_grid import create_processor_grid
from ..core import parallel
from ..resources import CONFIG 
from ..support.flow import Flow, Options

# external libraries
import numpy
import h5py # type: ignore

# define public interface
__all__ = ['calc_flows', 'write_flows', ]

# static analysis
if TYPE_CHECKING:
    from typing import Any, Dict, Tuple
    from collections.abc import MutableSequence, Sequence, Sized
    N = numpy.ndarray
    M = MutableSequence[N]
    Coords = Tuple[N, N, N]
    Blocks = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]]

# define configuration constants (internal)
FIELDS = CONFIG['create']['block']['fields']
NAME = CONFIG['create']['block']['name']

@parallel.safe
def calc_flows(*, blocks: Blocks, method: str, options: dict[str, Any], path: str, 
               procs: tuple[int, int, int]) -> tuple[dict[str, N], Index]:
    """Calculate desired initial flow fields; dispatches appropriate method using local blocks."""

    # create grid init parameters for parallelizing blocks 
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(*procs)
    gr_numProcs = int(numpy.prod(gr_axisNumProcs))
    gr_lIndex = parallel.Index.from_simple(gr_numProcs)
    gr_lMesh = gr_lIndex.mesh_width(gr_axisMesh)

    # create flow field parameters
    gr_flow = flow(method, Options(path, **options))

    # create flow fields
    return gr_flow.flow(blocks=blocks, mesh=gr_lMesh), gr_lIndex

@parallel.safe
def write_flows(*, fields: dict[str, N], shapes: dict[str, tuple[int, ...]], path: str, index: Index) -> None:
    
    # auto fill missing supported fields
    keys = fields.keys()
    first = next(iter(fields))
    for default, shape in FIELDS.items():
        if default not in keys:
            fields[default] = numpy.zeros(shapes[shape], dtype=float)

    # specify filename and remove if exists
    filename = os.path.join(path, NAME)
    if parallel.is_root() and os.path.exists(filename): 
        os.remove(filename)

    if parallel.is_serial():

        # write hdf5 file serially
        with h5py.File(filename, 'w-') as h5file:
            for field, data in fields.items():
                h5file.create_dataset(field, data=data)
    
    else:
        comm = parallel.COMM_WORLD
        shape = (shapes['center'][0], ) + data.shape[1:] 
        
        # write hdf5 file with parallel support
        if 'mpio' in h5py.registered_drivers():
            with h5py.File(filename, 'w-', driver='mpio', comm=comm) as h5file:
                for field, data in fields.items():
                    dset = h5file.create_dataset(field, shape, dtype=data.dtype)
                    dset[index.low:index.high+1] = data
        
        else:

            # write hdf5 file without parallel support
            if parallel.is_root(): 
                h5file = h5py.File('parallel.h5', 'w-')
            for field, data in fields.items():
                if parallel.is_root():
                    dset = h5file.create_dataset(field, shape, dtype=data.dtype)
                for process in range(index.size):
                    low, high = None, None
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
