"""Create an initial simulation domain (grid) hdf5 file."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os
import sys
import re

# internal libraries
from ...core.error import AutoError
from ...core.logging import printer
from ...core.parallel import single
from ...core.progress import get_bar
from ...core.stream import Instructions, mail
from ...library.create_grid import calc_coords, write_coords
from ...resources import CONFIG, DEFAULTS

# static analysis
if TYPE_CHECKING:
    from ...core.stream import S

# define public interface
__all__ = ['grid', ]

# define default constants

# default constants for handling the argument stream
PACKAGES = {}
ROUTE = ('create', 'grid')
PRIORITY = {}
CRATES = (adapt_arguments, attach_context, log_messages)
DROPS = {}
MAPPING = {}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: S) -> S:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

def grid(**arguments: S) -> None:
    """Python application interface for creating a initial grid file from command line or python code.

    Keyword arguments:
    nxb: int      Number of grid points per block in the i direction; defaults to {create_grid.NXB}
    nyb: int      Number of grid points per block in the j direction; defaults to {create_grid.NYB}
    nzb: int      Number of grid points per block in the k direction; defaults to {create_grid.NZB}
    iProcs: int   Number of blocks in the i direction; defaults to {create_grid.IPROCS}
    jProcs: int   Number of blocks in the j direction; defaults to {create_grid.JPROCS}
    kProcs: int   Number of blocks in the k direction; defaults to {create_grid.KPROCS}
