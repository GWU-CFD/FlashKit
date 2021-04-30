"""Supporting type annotations for support and library sub-packages."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# static analysis
if TYPE_CHECKING:
   
    # standard libraries
    from typing import Dict, Optional, Tuple
    from collections.abc import MutableSequence, Sequence

    # external libraries
    import numpy

    # grid arrays (and collections)
    N = numpy.ndarray
    M = MutableSequence[N]
    Blocks = Dict[str, N]
    Coords = Tuple[N, N, N]
    Faces = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]]
    Grids = Dict[str, Tuple[Optional[N], ...]]
    Mesh = Sequence[Tuple[int, ...]]
    Shapes = Dict[str, Tuple[int, ...]]

    # xdmf tag annotations
    TagAttr = Tuple[str, Dict[str, str]]
    TagAttrEx = Tuple[str, Dict[str, str], str]

# deal w/ runtime cast and import
else:

    # grid arrays (and collections)
    N = None
    M = None
    Blocks = None
    Coords = None
    Faces = None
    Grids = None
    Mesh = None
    Shapes = None

    # xdmf tag annotations
    TagAttr = None
    TagAttrEx = None

