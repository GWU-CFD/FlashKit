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
    from collections.abc import Container, MutableSequence, Sequence
    N = numpy.ndarray
    M = MutableSequence[N]
    C = Container[int]
    I = Iterable[int]
    F = Iterable[float]
    S = Sequence[str]

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

def int_safe(value):
    """Provide pythonic int conversion that fails to str."""
    try: return int(value)
    except ValueError: return str(value)

def from_ascii(*, source: Iterable[str], column: Iterable[int], delimiter: Iterable[Union[str, int]], header: Iterable[int]) -> Callable[..., None]:
    """Factory method for implementing a ascii file interface for stretching algorithms."""
    def wrapper(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F) -> None:
        for axis, (s, c, d, h) in enumerate(zip(source, column, delimiter, header)):
            if axis < ndim and axis in axes:
                coords[axis] = numpy.genfromtxt(fname=s, usecols=(c, ), delimiter=d, skip_header=h, dtype=numpy.float_)   
    return wrapper

def from_python(*, path: Iterable[str], source: Iterable[str], function: Iterable[str]) -> Callable[..., None]:
    """Factory method for implementing a python interface for stretching algorithms."""
    def wrapper(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F) -> None:
        for axis, (p, s, f) in enumerate(zip(path, source, function)):
            if axis < ndim and axis in axes:
                loader = importlib.machinery.SourceFileLoader(s, os.path.join(p, s + '.py'))
                spec = importlib.util.spec_from_loader(loader.name, loader)
                module = importlib.util.module_from_spec(spec)
                loader.exec_module(module)
                getattr(module, f)(axes, coords, sizes, ndim, smin, smax)
    return wrapper

def uniform(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F) -> None:
    """Method implementing a uniform grid algorithm."""
    for axis, (size, start, end) in enumerate(zip(sizes, smin, smax)):
        if axis < ndim and axis in axes:
            coords[axis] = numpy.linspace(start, end, size + 1)

def tanh_mid(*, axes: C, coords: M, sizes: I, ndim: int, smin: F, smax: F, alpha: F) -> None:
    """Method implementing a symmetric hyperbolic tangent stretching algorithm."""
    for axis, (size, start, end, a) in enumerate(zip(sizes, smin, smax, alpha)):
        if axis < ndim and axis in axes:
            coords[axis] = (end - start) * (numpy.tanh((-1.0 + 2.0 * numpy.linspace(0.0, 1.0, size + 1)) * numpy.arctanh(a)) / a + 1.0) / 2.0 + start

@dataclass
class Parameters:
    root: InitVar[str]

    alpha: Union[dict, N] = field(default_factory=dict)
    column: Union[dict, Iterable[int]] = field(default_factory=dict)
    delimiter: Union[dict, Iterable[Union[str, int]]] = field(default_factory=dict)
    header: Union[dict, Iterable[int]] = field(default_factory=dict)
    function: Union[dict, Iterable[str]] = field(default_factory=dict)
    path: Union[dict, Iterable[str]] = field(default_factory=dict)
    source: Union[dict, Iterable[str]] = field(default_factory=dict)

    def __post_init__(self, root):
        self.alpha = numpy.array([float(self.alpha.get(key, default)) for key, default in ALPHA.items()])
        self.column = [int(self.column.get(key, default)) for key, default in COLUMN.items()]
        self.delimiter = [int_safe(self.delimiter.get(key, default)) for key, default in DELIMITER.items()]
        self.function = [str(self.function.get(key, default)) for key, default in FUNCTION.items()]
        self.header = [int(self.header.get(key, default)) for key, default in HEADER.items()]
        self.path = [str(self.path.get(key, root)) for key in AXES]
        self.source = [str(self.source.get(key, default)) for key, default in SOURCE.items()]

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
                'python': from_python(path=parameters.path, source=parameters.source, function=parameters.function), 
                'uniform': uniform,
                'tanh_mid': partial(tanh_mid, alpha=parameters.alpha),
                        }
