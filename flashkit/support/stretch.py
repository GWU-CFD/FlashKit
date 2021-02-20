"""Support methods providing available stretching algorithms."""

# type annotations
from __future__ import annotations
from typing import cast, TYPE_CHECKING

# standard libraries
from dataclasses import dataclass, field, InitVar
from functools import partial

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

# define public interface
__all__ = ['Parameters', 'Stretching', ]

# define default constants
AXES = ('i', 'j', 'k')
ALPHA = dict(zip(AXES, CONFIG['support']['stretch']['alpha'])) 

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
    alpha: Union[dict, N] = field(default_factory=dict)
    
    def __post_init__(self):
        self.alpha = numpy.array([self.alpha.get(key, default) for key, default in ALPHA.items()])

@dataclass
class Stretching:
    methods: InitVar[S]
    parameters: InitVar[Parameters]
            
    map_axes: Callable[[Any, str], list[int]] = field(repr=False, init=False)
    any_axes: Callable[[Any, str], bool] = field(repr=False, init=False)
    stretch: dict[str, Callable[..., None]] = field(repr=False, init=False)
    default: str = 'uniform'
    
    def __post_init__(self, methods, parameters):
        self.map_axes = lambda _, check: [axis for axis, method in enumerate(methods) if method == check]
        self.any_axes = lambda _, check: any(method == check for method in methods)
        self.stretch = {'uniform': uniform,
                        'tanh_mid': partial(tanh_mid, params=parameters.alpha)}
