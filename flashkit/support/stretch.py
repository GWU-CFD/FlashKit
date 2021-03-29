"""Support methods providing available stretching algorithms."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
import os
from dataclasses import dataclass, field, InitVar
from functools import partial
import importlib

# internal libraries
from ..resources import CONFIG

# external libraries
import numpy

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, Iterable, Union, TypeVar
    from collections.abc import Container, Mapping, MutableSequence, Sequence
    N = numpy.ndarray
    M = MutableSequence[N]
    C = Container[int]
    I = Iterable[int]
    F = Iterable[float]
    S = Sequence[str]
    D = Mapping[str, Any]

# define library (public) interface
__all__ = ['Stretching', ]

# define configuration constants (internal)
AXES = tuple(CONFIG['create']['grid']['axes'])
METHODS = CONFIG['support']['stretch']['methods']

# define default paramater configuration constants (internal)
ALPHA = CONFIG['support']['stretch']['alpha']
COLUMN = tuple(CONFIG['support']['stretch']['column'])
DELIMITER = CONFIG['support']['stretch']['delimiter']
HEADER = CONFIG['support']['stretch']['header']
FUNCTION = tuple(CONFIG['support']['stretch']['function'])
SOURCE = CONFIG['support']['stretch']['source']

def from_ascii(*, source: Iterable[str], column: Iterable[int], delimiter: Iterable[Union[str, int]], header: Iterable[int]) -> Callable[..., None]:
    """Factory method for implementing a ascii file interface for stretching algorithms."""
    def wrapper(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F) -> None:
        for axis, (s, c, d, h) in enumerate(zip(source, column, delimiter, header)):
            if axis < ndim and axis in axes:
                coords[axis] = numpy.genfromtxt(fname=s, usecols=(c, ), delimiter=d, skip_header=h, dtype=numpy.float_)   
    return wrapper

def from_python(*, path: Iterable[str], source: Iterable[str], function: Iterable[str], options: Mapping[str, Any]) -> Callable[..., None]:
    """Factory method for implementing a python interface for stretching algorithms."""
    def wrapper(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F) -> None:
        for axis, (p, s, f, size, low, high) in enumerate(zip(path, source, function, sizes, smin, smax)):
            if axis < ndim and axis in axes:
                loader = importlib.machinery.SourceFileLoader(s, os.path.join(p, s + '.py'))
                spec = importlib.util.spec_from_loader(loader.name, loader)
                module = importlib.util.module_from_spec(spec)
                loader.exec_module(module)
                kwargs = {kwarg: value[axis] for kwarg, value in options.items() if value[axis]}
                coords[axis] = getattr(module, f)(size, low, high, **kwargs)
    return wrapper

def uniform(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F) -> None:
    """Method implementing a uniform grid algorithm."""
    for axis, (size, low, high) in enumerate(zip(sizes, smin, smax)):
        if axis < ndim and axis in axes:
            coords[axis] = numpy.linspace(low, high, size + 1)

def tanh_mid(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F, alpha: F) -> None:
    """Method implementing a symmetric hyperbolic tangent stretching algorithm."""
    for axis, (size, low, high, a) in enumerate(zip(sizes, smin, smax, alpha)):
        if axis < ndim and axis in axes:
            coords[axis] = (high - low) * (numpy.tanh((-1.0 + 2.0 * numpy.linspace(0.0, 1.0, size + 1)) * numpy.arctanh(a)) / a + 1.0) / 2.0 + low

class Stretching:
    """Class supporting the dispatching of axes to methods to build the grid."""
    methods: S
    stretch: dict[str, Callable[..., None]]
    
    def __init__(self, methods: S, root: str, *, alpha: D = {}, column: D = {}, delimiter: D = {},
                 function: D = {}, header: D = {}, path: D = {}, source: D = {}, **kwargs):

        assert all(method in METHODS for method in methods), 'Unkown Stretching Method Specified!'
        self.methods = methods
        
        # fully specify function parameters with defaults if none provided
        s_alpha = numpy.array([alpha.get(key, ALPHA) for key in AXES])
        s_column = [column.get(key, default) for key, default in zip(AXES, COLUMN)]
        s_delimiter = [delimiter.get(key, DELIMITER) for key in AXES]
        s_function = [function.get(key, default) for key, default in zip(AXES, FUNCTION)]
        s_header = [header.get(key, HEADER) for key in AXES]
        s_path = [path.get(key, root) for key in AXES]
        s_source = [source.get(key, SOURCE) for key in AXES]
        s_meta = {kwarg: [value.get(key, None) for key in AXES] for kwarg, value in kwargs.items()}

        self.stretch = {
                'ascii': from_ascii(source=[os.path.join(p, s) for p, s in zip(s_path, s_source)], 
                                    column=s_column, delimiter=s_delimiter, header=s_header), 
                'python': from_python(path=s_path, source=s_source, function=s_function, options=s_meta), 
                'uniform': uniform,
                'tanh_mid': partial(tanh_mid, alpha=s_alpha),
                        }

    def map_axes(self, check: str) -> list[int]:
        """Which axes does this method need to handle."""
        return [axis for axis, method in enumerate(self.methods) if method == check]
    
    def any_axes(self, check: str) -> bool:
        """Does this method need to deal with any axes."""
        return any(method == check for method in self.methods)
