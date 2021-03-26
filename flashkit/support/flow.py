"""Support methods providing available flow field initialization algorithms."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os
from functools import partial
import importlib

# internal libraries
from ..resources import CONFIG

# external libraries
import numpy

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, Iterable, Union, Tuple
    from collections.abc import Container, Mapping, MutableSequence, Sequence
    N = numpy.ndarray
    M = MutableMapping[str, N]
    D = Mapping[str, Any]
    F = Mapping[str, str]
    G = Mapping[str, Tuple[N, N, N]]
    S = Mapping[str, Tuple[int, ...]]
    I = Sequence[Tuple[int, int, int]]

# define library (public) interface
__all__ = ['Parameters', 'flow', ]

# define configuration constants (internal)
METHODS = CONFIG['support']['flow']['methods']

# define default paramater configuration constants (internal)
FUNCTION = CONFIG['support']['flow']['function']
LEVEL = CONFIG['support']['flow']['level']
SOURCE = CONFIG['support']['flow']['source']

def constant(*, blocks: M, fields: F, grids: G, mesh: I, shapes: S, level: dict[str, float]) -> None:
    """Method implementing a constant value field initialization."""
    for field, location in fields.items():
        shape = (len(index), ) + shapes[location][1:]
        const = level[field]
        blocks[field] = numpy.ones(shape, dtype=float) * const

def uniform(*, blocks: M, fields: F, grids: G, mesh: I, shapes: S) -> None:
    """Method implementing a uniform (zero) field initialization."""
    for field, location in fields.items():
        shape = (len(index), ) + shapes[location][1:]
        blocks[field] = numpy.zeroes(shape, dtype=float)
        
class Parameters:
    fields: dict[str, str]
    function: dict[str, str]
    level: dict[str, float]
    path: dict[str, str]
    source: dict[str, str]
    meta: dict[str, dict[str, Any]]

    def __init__(self, root: str, fields: S, *, 
                 function: D = {}, level: D = {}, path: D = {}, source: S = {}, 
                 **kwargs) -> None:
        assert all(grid in GRIDS for grid in fields.values()), 'Unknown Grid Specified for a Given Field!'
        keys = fields.keys()
        self.fields = dict(fields)
        self.function = {key: function.get(key, FUNCTION) for key in keys}
        self.path = {key: path.get(key, root) for key in keys}
        self.source = {key: source.get(key, SOURCE) for key in keys}
        self.level = {key: level.get(key, LEVEL) for key in keys}
        self.meta = {kwarg: {key: value.get(key, None) for key in keys} for kwarg, value in kwargs.items()}

class Flowing:
    map_fields: Callable[[Any, str], set[str]] 
    any_fields: Callable[[Any, str], bool]
    flow: dict[str, Callable[..., None]]

    def __init__(self, methods: S, parameters: Parameters):
        assert all(method in METHODS for method in methods), 'Unknown Flow Initiation Method Specified!'
        self.flow = {
            'constant': partial(constant, level=parameters.level), 
            'uniform': uniform, 
                    }
