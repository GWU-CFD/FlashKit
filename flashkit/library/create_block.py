"""Create an initial simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..core.parallel import safe, squash
from ..resources import CONFIG 
#from ..support.flow import FlowFields 

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
