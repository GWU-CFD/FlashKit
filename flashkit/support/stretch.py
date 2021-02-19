"""Support methods providing available stretching algorithms."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# standard libraries
from dataclasses import dataclass, field, InitVar
from functools import partial

# internal libraries
from ..resources import CONFIG

# external libraries
import numpy # type: ignore

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, Union, TypeVar
    from collections.abc import Sequence, MutableSequence
    D = Union[int, float]
    S = Sequence[D]
    M = MutableSequence[D]
    C = MutableSequence[M]

# define public interface
__all__ = ['Parameters', 'Stretching', ]

# define default constants
AXES = ('i', 'j', 'k')
ALPHA = dict(zip(AXES, CONFIG['support']['stretch']['alpha'])) 

def uniform(*, axes: S, coords: C, sizes: S, ndim: int, smin: S, smax: S) -> None:
    """Method implementing a uniform grid algorithm."""
    for axis, (size, start, end) in enumerate(zip(sizes, smin, smax)):
        if axis < ndim and axis in axes:
            coords[axis] = numpy.linspace(start, end, size + 1)

def tanh_mid(*, axes: S, coords: C, sizes: S, ndim: int, smin: S, smax: S, params: S) -> None:
    """Method implementing a symmetric hyperbolic tangent stretching algorithm."""
    for axis, (size, start, end, p) in enumerate(zip(sizes, smin, smax, params)):
        if axis < ndim and axis in axes:
            coords[axis] = (end - start) * (numpy.tanh((-1.0 + 2.0 * numpy.linspace(0.0, 1.0, size + 1)) * numpy.arctanh(p)) / p + 1.0) / 2.0 + start

@dataclass
class Parameters:
    alpha: Union[dict, S] = field(default_factory=dict)
    
    def __post_init__(self):
        self.alpha = numpy.array([self.alpha.get(key, default) for key, default in ALPHA.items()])

@dataclass
class Stretching:
    methods: InitVar[Sequence[str]]
    parameters: InitVar[Parameters]
            
    map_axes: Callable[[str], list[int]] = field(repr=False, init=False)
    any_axes: Callable[[str], bool] = field(repr=False, init=False)
    stretch: dict[str, Callable[[Any], None]] = field(repr=False, init=False)
    default: str = 'uniform'
    
    def __post_init__(self, methods, parameters):
        self.map_axes = lambda stretch: [axis for axis, method in enumerate(methods) if method == stretch]
        self.any_axes = lambda stretch: len(self.map_axes(stretch)) > 0
        self.stretch = {'uniform': uniform,
                        'tanh_mid': partial(tanh_mid, params=parameters.alpha)}
