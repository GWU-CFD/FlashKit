"""Supporting type annotations for support and library sub-packages."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# static analysis
if TYPE_CHECKING:
   
    # standard libraries
    from typing import Any, Dict, List, Optional, Tuple
    from collections.abc import MutableSequence, Sequence

    # external libraries
    import numpy
    import h5py # type: ignore

    # grid arrays (and collections)
    D = h5py._hl.dataset.Dataset
    N = numpy.ndarray
    M = MutableSequence[N]
    Blocks = Dict[str, N]
    Coords = Tuple[N, N, N]
    Faces = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]]
    Grids = Dict[str, Tuple[Optional[N], ...]]
    Mesh = Sequence[Tuple[int, ...]]
    Shapes = Dict[str, Tuple[int, ...]]

    # par annotations
    Sections = Dict[str, Any]
    Lines = List[str]
    Template = Dict[str, Sections]  

    # xdmf tag annotations
    TagAttr = Tuple[str, Dict[str, str]]
    TagAttrEx = Tuple[str, Dict[str, str], str]

# deal w/ runtime cast and import
else:

    # grid arrays (and collections)
    D = None
    N = None
    M = None
    Blocks = None
    Coords = None
    Faces = None
    Grids = None
    Mesh = None
    Shapes = None

    # par annotations
    Sections = None
    Lines = None
    Template = None  

    # xdmf tag annotations
    TagAttr = None
    TagAttrEx = None

