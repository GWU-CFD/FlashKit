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
from .types import N

# external libraries
import numpy

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, Tuple 
    from collections.abc import Mapping, MutableMapping, Sequence
    M = MutableMapping[str, N]
    D = Mapping[str, str]
    F = Mapping[str, float]
    G = Mapping[str, Tuple[N, N, N]]
    S = Mapping[str, Tuple[int, ...]]
    I = Sequence[Tuple[int, ...]]

# define library (public) interface
__all__ = ['Flowing', ]

# define configuration constants (internal)
METHODS = CONFIG['support']['flow']['methods']

# define default paramater configuration constants (internal)
CONST = CONFIG['support']['flow']['const']
FREQ = CONFIG['support']['flow']['freq']
SHIFT = CONFIG['support']['flow']['shift']
SCALE = CONFIG['support']['flow']['scale']
FUNCTION = CONFIG['support']['flow']['function']
SOURCE = CONFIG['support']['flow']['source']

def constant(*, blocks: M, fields: D, grids: G, mesh: I, shapes: S, const: dict[str, float]) -> None:
    """Method implementing a constant value field initialization."""
    for field, location in fields.items():
        blocks[field] = numpy.ones(shapes[location], dtype=float) * const[field]

def stratified(*, blocks: M, fields: D, grids: G, mesh: I, shapes: S, const: F, scale: F, shift: F) -> None:
    """Method implementing a cold over hot intial condition."""
    ndim = 2 if all(g[2] is None for g in grids.values()) else 3
    for field, location in fields.items():
        source = grids[location][ndim - 1]
        meshed = [m[ndim - 1] for m in mesh]
        sliced = (slice(None), None, slice(None), None) if ndim == 2 else (slice(None), slice(None), None, None)
        domain = numpy.heaviside(numpy.array([source[m,:] for m in meshed]) - shift[field], 0.5) * scale[field] + const[field]
        blocks[field] = numpy.ones(shapes[location], dtype=float) * domain[sliced]

def uniform(*, blocks: M, fields: D, grids: G, mesh: I, shapes: S) -> None:
    """Method implementing a uniform (zero) field initialization."""
    for field, location in fields.items():
        blocks[field] = numpy.zeros(shapes[location], dtype=float)

class Flowing:
    """Class supporting the dispatching of fields to methods to build initial flow condition."""
    methods: dict[str, str]
    flow: dict[str, Callable[..., None]]

    def __init__(self, methods: D, root: str, *, const: D = {}, freq: D = {}, shift: D = {}, scale: D = {},
                 function: D = {}, path: D = {}, source: D = {}, **kwargs):
    
        assert all(method in METHODS for method in methods.values()), 'Unknown Flow Initiation Method Specified!'
        self.methods = dict(methods)
        keys = methods.keys()

        # fully specify the function parameters with defaults if none provided
        s_const = {key: const.get(key, CONST) for key in keys}
        s_freq = {key: freq.get(key, FREQ) for key in keys}
        s_shift = {key: shift.get(key, SHIFT) for key in keys}
        s_scale = {key: scale.get(key, SCALE) for key in keys}
        s_function = {key: function.get(key, FUNCTION) for key in keys}
        s_path = {key: path.get(key, root) for key in keys}
        s_source = {key: source.get(key, SOURCE) for key in keys}
        s_meta = {kwarg: {key: value.get(key, None) for key in keys} for kwarg, value in kwargs.items()}
        
        self.flow = {
            'constant': partial(constant, const=s_const), 
            'stratified': partial(stratified, const=s_const, scale=s_scale, shift=s_shift), 
            'uniform': uniform, 
                    }

    def map_fields(self, check: str) -> set[str]:
        """Which fields does this method need to handle."""
        return {field for field, method in self.methods.items() if method == check}

    def any_fields(self, check: str) -> bool:
        """Does this method need to deal with any fields."""
        return any(method == check for method in self.methods.values())
