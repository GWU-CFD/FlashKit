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
    S = Sequence[str]
    D = Mapping[str, Any]
    M = Sequence[Tuple[int, int, int]]
    Blocks = Tuple[Tuple[N, N, N], Tuple[N, N, N], Tuple[N, N, N]]

# define library (public) interface
__all__ = ['Parameters', 'flow', ]

# define configuration constants (internal)
METHODS = CONFIG['support']['flow']['methods']

# define default paramater configuration constants (internal)
FIELDS = CONFIG['support']['flow']['fields']
LEVEL = CONFIG['support']['flow']['level']
FUNCTION = CONFIG['support']['flow']['function']
SOURCE = CONFIG['support']['flow']['source']

def from_python(*, path: Iterable[str], source: Iterable[str], function: Iterable[str], options: Mapping[str, Any]) -> Callable[..., dict[str, N]]:
    """Factory method for implementing a python interface for flow intialization algorithms."""
    pass

def uniform(*, blocks: Blocks, mesh: M, level: dict[str, float]) -> dict[str, N]:
    pass

class Parameters:
    fields: dict[str, str]
    function: str
    level: dict[str, float]
    path: str
    source: str
    meta: dict[str, Any]

    def __init__(self, path: str, *, function: str = FUNCTION, source: str = SOURCE, 
                 fields: D = {}, level: D = {}, **kwargs) -> None:
        self.function = function
        self.path = path
        self.source = source
        self.fields = {**FIELDS, **fields}
        self.level = {**LEVEL, **level}
        self.meta = {kwarg: value for kwarg, value in kwargs.items()}

def flow(method: str, parameters: Parameters) -> Callable[..., dict[str, N]]:
    assert method in METHODS, 'Unknown Flow Initiation Method Specified!'
    flows: dict[str, Callable[..., dict[str, N]]] = {
        'python': from_python(path=parameters.path, source=parameters.source, function=parameters.function, options=parameters.meta),
        'uniform': partial(uniform, level=parameters.level), }
    return flows[method]
