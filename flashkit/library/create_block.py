"""Create an initial simulation flow field (block) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os

# internal libraries
from ..core import parallel
from ..resources import CONFIG, DEFAULTS 
from ..support.flow import FlowField

# external libraries
import numpy
import h5py

# define public interface
__all__ = ['calc_flows', 'write_flows', ]

if TYPE_CHECKING:
    from typing import Union
    Vector = numpy.ndarray
    Coords = tuple[Vector, Vector, Vector]
    Blocks = tuple[Coords, Coords, Coords]

# define default constants
PATH = DEFAULTS['general']['paths']['working']
METHOD = CONFIG['create']['init']['method']
NAME = CONFIG['create']['init']['name']
