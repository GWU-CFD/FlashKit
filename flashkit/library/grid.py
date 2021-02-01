"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import Tuple, List, Dict, Union, TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..resources import CONFIG, DEFAULTS 
from ..support.stretch import Stretching, Parameters 

# external libraries
import numpy
import h5py

# define public interface
__all__ = ['calc_coords', 'get_blocks', 'get_shapes', 'write_coords', ]

if TYPE_CHECKING:
    NDA = numpy.ndarray
    COORDS = Tuple[NDA, NDA, NDA]
    BLOCKS = Tuple[Tuple[NDA, NDA, NDA], 
                   Tuple[NDA, NDA, NDA], 
                   Tuple[NDA, NDA, NDA]]

# define default constants
MDIM = CONFIG['create']['grid']['mdim']
NDIM = DEFAULTS['create']['grid']['ndim']
SIZE = DEFAULTS['create']['grid']['size']
SMIN = CONFIG['create']['grid']['smin']
SMAX = CONFIG['create']['grid']['smax']
METHOD = CONFIG['create']['grid']['method']
NAME = CONFIG['create']['grid']['name']
PATH = DEFAULTS['general']['paths']['working']

def calc_coords(*, param: Dict[str, Dict[str, Union[int, float]]] = {}, procs: Dict[str, int] = {},
                simmn: Dict[str, float] = {}, simmx: Dict[str, float] = {}, sizes: Dict[str, int] = {}, 
                stype: Dict[str, str] = {}, ndims: int = NDIM) -> COORDS:
    """Calculate global coordinate axis arrays; face data vice cell data."""

    # create grid init parameters
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(**procs)
    gr_min, gr_max = create_bounds(mins=simmn, maxs=simmx)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(**sizes, ijkProcs=gr_axisNumProcs)
    gr_ndim = ndims

    # create grid stretching parameters
    gr_strBool, gr_strType = create_stretching(methods=stype)
    gr_str = Stretching(gr_strType, Parameters(**param))

    # Create grids
    return tuple(get_filledCoords(sizes=gr_gIndexSize, methods=gr_str, ndim=gr_ndim, smin=gr_min, smax=gr_max))

def get_blocks(coordinates: COORDS, *, procs: Dict[str, int] = {}, sizes: Dict[str, int] = {}) -> BLOCKS: 
    """Calculate block coordinate axis arrays from global axis arrays."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(**procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(**sizes, ijkProcs=gr_axisNumProcs)
    xfaces, yfaces, zfaces = coordinates

    # calculate the iaxis block coordinates
    lIndex = gr_lIndexSize[0]
    xxxl = numpy.array([xfaces[0 + i * lIndex:0 + (i + 1) * lIndex] for i, _, _ in gr_axisMesh])
    xxxr = numpy.array([xfaces[1 + i * lIndex:1 + (i + 1) * lIndex] for i, _, _ in gr_axisMesh])
    xxxc = (xxxr + xxxl) / 2.0

    # calculate the jaxis block coordinates
    lIndex = gr_lIndexSize[1]
    yyyl = numpy.array([yfaces[0 + j * lIndex:0 + (j + 1) * lIndex] for _, j, _ in gr_axisMesh])
    yyyr = numpy.array([yfaces[1 + j * lIndex:1 + (j + 1) * lIndex] for _, j, _ in gr_axisMesh])
    yyyc = (yyyr + yyyl) / 2.0

    # calculate the kaxis block coordinates
    if zfaces is not None:
        lIndex = gr_lIndexSize[2]
        zzzl = numpy.array([zfaces[0 + k * lIndex:0 + (k + 1) * lIndex] for _, _, k in gr_axisMesh])
        zzzr = numpy.array([zfaces[1 + k * lIndex:1 + (k + 1) * lIndex] for _, _, k in gr_axisMesh])
        zzzc = (zzzr + zzzl) / 2.0
    else:
        zzzl, zzzr, zzzc = None, None, None

    return (xxxl, xxxc, xxxr), (yyyl, yyyc, yyyr), (zzzl, zzzc, zzzr)

def get_shapes(*, procs: Dict[str, int] = {}, sizes: Dict[str, int] = {}) -> Dict[str, Tuple[int, int, int]]:
    """Determine shape of simulation data on the relavent grids (e.g., center or facex)."""

    # get the processor communicator layout and global arrays
    gr_axisNumProcs, gr_axisMesh = create_processor_grid(**procs)
    gr_lIndexSize, gr_gIndexSize = create_indexSize_fromLocal(**sizes, ijkProcs=gr_axisNumProcs)
   
    # create shape data as dictionary
    shapes = {'center': tuple([gr_axisNumProcs.prod()] + gr_lIndexSize[::-1].tolist())}
    shapes['facex'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 0, 1))) 
    shapes['facey'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (0, 1, 0))) 
    shapes['facez'] = tuple([gr_axisNumProcs.prod()] + list(gr_lIndexSize[::-1] + (1, 0, 0))) 
    
    return shapes

def write_coords(coordinates: COORDS, *, path: str = PATH) -> None:
    """Write global coordinate axis arrays to an hdf5 file."""

    # specify path
    cwd = os.getcwd()
    path = cwd + '/' + path
    filename = path + NAME
    
    # create file
    with h5py.File(filename, 'w') as h5file:
        
        # write data to file
        for axis, coords in zip(('x', 'y', 'z'), coordinates):
            if coords is not None:
                h5file.create_dataset(axis + 'Faces', data=coords)

def create_bounds(*, mins: Dict[str, float]={}, maxs: Dict[str, float]={}):
    def_mins = {key: SMIN for key in ('i', 'j', 'k')}
    def_maxs = {key: SMAX for key in ('i', 'j', 'k')}
    simmn = [mins.get(key, default) for key, default in def_mins.items()]
    simmx = [maxs.get(key, default) for key, default in def_maxs.items()]
    return tuple(numpy.array(item, float) for item in (simmn, simmx))

def create_indexSize_fromGlobal(*, i: int = SIZE, j: int = SIZE, k: int = SIZE, ijkProcs: NDA):
    gSizes = [i, j, k]
    blocks = [size / procs for procs, size in zip(ijkProcs, gSizes)]
    return tuple(numpy.array(item, int) for item in (blocks, gSizes))

def create_indexSize_fromLocal(*, i: int = SIZE, j: int = SIZE, k: int = SIZE, ijkProcs: NDA):
    blocks = [i, j, k]
    gSizes = [procs * nb for procs, nb in zip(ijkProcs, blocks)]
    return tuple(numpy.array(item, int) for item in (blocks, gSizes))

def create_processor_grid(*, i: int = SIZE, j: int = SIZE, k: int = SIZE):
    iProcs, jProcs, kProcs = i, j, k
    proc = [iProcs, jProcs, kProcs]
    grid = [[i, j, k] for k in range(kProcs) for j in range(jProcs) for i in range(iProcs)]
    return tuple(numpy.array(item, int) for item in (proc, grid))

def create_stretching(*, methods: Dict[str, str] = {}):
    default = METHOD
    def_methods = {key: default for key in ('i', 'j', 'k')}
    strTypes = [methods.get(key, default) for key, default in def_methods.items()]
    strBools = [method != default for method in strTypes]
    return tuple(numpy.array(item) for item in (strBools, strTypes))

def get_blankCoords(sizes: NDA) -> List[NDA]:
    return [None] * len(sizes)

def get_filledCoords(*, sizes: NDA, methods: Stretching, ndim: int, smin: NDA, smax: NDA) -> List[NDA]:
    coords = get_blankCoords(sizes)

    for method, func in methods.stretch.items():
        if methods.any_axes(method):
            func(axes=methods.map_axes(method), coords=coords, sizes=sizes, ndim=ndim, smin=smin, smax=smax)

    return coords
