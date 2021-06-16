"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import Any, cast

# standard libraries
import os

# internal libraries
from ..core.parallel import Index, safe, single, squash
from ..resources import CONFIG 
from ..support.grid import axisMesh, indexSize_fromLocal
from ..support.stretch import Stretching
from ..support.types import N, M, Coords 

# external libraries
import numpy 
import h5py  # type: ignore

# define library (public) interface
__all__ = ['calc_coords', 'get_grids', 'get_shapes', 'read_coords', 'write_coords', ]

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
    gr_axisNumProcs, gr_axisMesh = axisMesh(*procs)
    gr_min, gr_max = numpy.array(smins, float), numpy.array(smaxs, float)
    gr_lIndexSize, gr_gIndexSize = indexSize_fromLocal(*sizes, gr_axisNumProcs)

    # create grid stretching parameters
    gr_str = Stretching(stypes, path, **params)

    # Create grids
    return get_filledCoords(sizes=gr_gIndexSize, methods=gr_str, ndim=ndim, smin=gr_min, smax=gr_max)

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

def get_filledCoords(*, sizes: N, methods: Stretching, ndim: int, smin: N, smax: N) -> Coords:
    """(internal) - fill coordinate axis array by iterating through methods."""
    
    # typing annotation for pre-length list
    coords: M = cast(M, [None, None, None])
    
    # fill by iterating over methods and dispatching
    for method, func in methods.stretch.items():
        if methods.any_axes(method):
            func(axes=methods.map_axes(method), coords=coords, sizes=sizes, ndim=ndim, smin=smin, smax=smax)
    
    # return as tuple 
    x, y, z = coords
    return x, y, z
