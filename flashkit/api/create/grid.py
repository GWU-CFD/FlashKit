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
    ndim: int     Number of simulation dimensions (i.e., 2 or 3); defaults to {create_grid.NDIM}.
    nxb: int      Number of grid points per block in the i direction; defaults to {create_grid.NXB}.
    nyb: int      Number of grid points per block in the j direction; defaults to {create_grid.NYB}.
    nzb: int      Number of grid points per block in the k direction; defaults to {create_grid.NZB}.
    iprocs: int   Number of blocks in the i direction; defaults to {create_grid.IPROCS}.
    jprocs: int   Number of blocks in the j direction; defaults to {create_grid.JPROCS}.
    kprocs: int   Number of blocks in the k direction; defaults to {create_grid.KPROCS}.
    xrange: list  Bounding points (e.g., [0.0, 1.0]) for i direction; defaults to {create_grid.XRANGE}.
    yyange: list  Bounding points (e.g., [0.0, 1.0]) for j direction; defaults to {create_grid.YRANGE}.
    zrange: list  Bounding points (e.g., [0.0, 1.0]) for k direction; defaults to {create_grid.ZRANGE}.
    bndbox: list  Bounding box pairs (e.g., [[0.0, 1.0], ...]) for each of i,j,k directions.
    xmethod: str  Stretching method for grid points in the i directions; defaults to {create_grid.XMETHOD}.
    ymethod: str  Stretching method for grid points in the j directions; defaults to {create_grid.YMETHOD}.
    zmethod: str  Stretching method for grid points in the k directions; defaults to {create_grid.ZMETHOD}.
    xparam: dict  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for i direction method.
    yparam: dict  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for j direction method.
    zparam: dict  Key/value pairs for paramaters (e.g., {'alpha': 0.5 ...}) used for k direction method.

