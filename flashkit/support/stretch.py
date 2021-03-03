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
from ..core.custom import SafeAny, SafeInt
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
__all__ = ['Parameters', 'Stretching', ]

# define configuration constants (internal)
AXES = tuple(CONFIG['create']['grid']['axes'])
METHODS = CONFIG['support']['stretch']['methods']

# define default paramater configuration constants (internal)
ALPHA = dict(zip(AXES, CONFIG['support']['stretch']['alpha']))
COLUMN = dict(zip(AXES, CONFIG['support']['stretch']['column']))
DELIMITER = dict(zip(AXES, [',', ',', ',']))
HEADER = dict(zip(AXES, CONFIG['support']['stretch']['header']))
FUNCTION = dict(zip(AXES, CONFIG['support']['stretch']['function']))
SOURCE = dict(zip(AXES, CONFIG['support']['stretch']['source']))

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

class Parameters:
    alpha: N
    column: list[int]
    delimiter: list[Union[str, int]]
    function: list[str]
    header: list[int]
    path: list[str]
    source: list[str]
    meta: dict[str, list[Any]]

    def __init__(self, root: str, *, alpha: D = {}, 
                 column: D = {}, delimiter: D = {}, header: D = {}, function: D = {}, path: D = {}, source: D = {}, 
                 **kwargs) -> None:
        self.alpha = numpy.array([float(alpha.get(key, default)) for key, default in ALPHA.items()])
        self.column = [int(column.get(key, default)) for key, default in COLUMN.items()]
        self.delimiter = [SafeInt(delimiter.get(key, default)) for key, default in DELIMITER.items()]
        self.function = [str(function.get(key, default)) for key, default in FUNCTION.items()]
        self.header = [int(header.get(key, default)) for key, default in HEADER.items()]
        self.path = [str(path.get(key, root)) for key in AXES]
        self.source = [str(source.get(key, default)) for key, default in SOURCE.items()]
        self.meta = {kwarg: [SafeAny(value.get(key, None)) for key in AXES] for kwarg, value in kwargs.items()}

@dataclass
class Stretching:
    methods: InitVar[S]
    parameters: InitVar[Parameters]
            
    map_axes: Callable[[Any, str], list[int]] = field(repr=False, init=False)
    any_axes: Callable[[Any, str], bool] = field(repr=False, init=False)
    stretch: dict[str, Callable[..., None]] = field(repr=False, init=False)
    
    def __post_init__(self, methods, parameters):
        assert all(method in METHODS for method in methods), 'Unkown Stretching Method Specified!'
        self.map_axes = lambda check: [axis for axis, method in enumerate(methods) if method == check]
        self.any_axes = lambda check: any(method == check for method in methods)
        self.stretch = {
                'ascii': from_ascii(source=[os.path.join(p, s) for p, s in zip(parameters.path, parameters.source)], 
                                    column=parameters.column, delimiter=parameters.delimiter, header=parameters.header), 
                'python': from_python(path=parameters.path, source=parameters.source, function=parameters.function, options=parameters.meta), 
                'uniform': uniform,
                'tanh_mid': partial(tanh_mid, alpha=parameters.alpha),
                        }
