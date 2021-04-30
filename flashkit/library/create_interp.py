"""Create an initial flow field (block) using interpolated simulation data."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..core import parallel
from ..core.logging import printer
from ..resources import CONFIG 

# external libraries
import numpy
from scipy.interpolate import interpn # type: ignore
import h5py # type: ignore

# define public interface
__all__ = ['interp_blocks', ]

# static analysis
if TYPE_CHECKING:
    from typing import Dict, Optional, Tuple
    from ..core.progress import Bar
    N = numpy.ndarray
    Grids = Dict[str, Tuple[Optional[N], ...]]
    Shapes = Dict[str, Tuple[int, ...]]

# define configuration constants (internal)
BNAME = CONFIG['create']['block']['name']
GNAME = CONFIG['create']['grid']['name']

@parallel.safe
def interp_blocks(*, basename: str, checkname: str, dest: str, flows: dict[str, tuple[str, str]], gridname: str, grids: Grids,
                  method: str, plotname: str, procs: tuple[int, int, int], shapes: Shapes, source: str, step: int, context: Bar) -> None:
    """Interpolate desired initial flow fields from a simulation output to another computional grid."""
    
    # define necessary filenames on the correct path
    low_plot_name = os.path.join(source, basename + plotname + f'{step:04}')
    low_grid_name = os.path.join(source, basename + gridname + '0000')
    high_blk_name = os.path.join(os.path.relpath(source, dest), BNAME)
    high_grd_name = os.path.join(os.path.relpath(source, dest), GNAME)

    

def blocks_from_bbox(boxes, box):
    overlaps = lambda ll, lh, hl, hh: not ((hh < ll) or (hl > lh))
    #return [blk from blk, bb in enumerate(boxes) 
    #        if all(overlaps(*low, *high) for low, high in zip(bb, box))]


