"""Support methods providing available stretching algorithms."""

# type annotations
from __future__ import annotations
from typing import Any, Callable, Dict, Union, TYPE_CHECKING

# standard libraries
from dataclasses import dataclass, field, InitVar
from functools import partial

# external libraries
import numpy

# define public interface
__all__ = ['Parameters', 'Stretching', 'tanh_mid', 'uniform', ]

if TYPE_CHECKING:
    NDA = numpy.ndarray

def uniform(*, axes: NDA, coords: NDA, sizes: NDA, ndim: int, smin: NDA, smax: NDA) -> None:
    """Method implementing a uniform grid algorithm."""
    for axis, (size, start, end) in enumerate(zip(sizes, smin, smax)):
        if axis < ndim and axis in axes:
            coords[axis] = numpy.linspace(start, end, size + 1)

def tanh_mid(*, axes: NDA, coords: NDA, sizes: NDA, ndim: int, smin: NDA, smax: NDA, params: NDA) -> None:
    """Method implementing a symmetric hyperbolic tangent stretching algorithm."""
    for axis, (size, start, end, p) in enumerate(zip(sizes, smin, smax, params)):
        if axis < ndim and axis in axes:
            coords[axis] = (end - start) * (numpy.tanh((-1.0 + 2.0 * numpy.linspace(0.0, 1.0, size + 1)) * numpy.arctanh(p)) / p + 1.0) / 2.0 + start

@dataclass
class Parameters:
    alpha: Union[Dict, numpy.ndarray] = field(default_factory=dict)
    
    def __post_init__(self):
        def_alpha = {'i': 0.5, 'j': 0.5, 'k': 0.5}
        self.alpha = numpy.array([self.alpha.get(key, default) for key, default in def_alpha.items()])
        
@dataclass
class Stretching:
    methods: InitVar[numpy.ndarray] # length mdim specifying strType
    parameters: InitVar[Parameters]
            
    map_axes: Callable[[str], List[int]] = field(repr=False, init=False)
    any_axes: Callable[[str], bool] = field(repr=False, init=False)
    stretch: Dict[str, Callable[[Any], None]] = field(repr=False, init=False)
    default: str = 'uniform'
    
    def __post_init__(self, methods, parameters):
        self.map_axes = lambda stretch: [axis for axis, method in enumerate(methods) if method == stretch]
        self.any_axes = lambda stretch: len(self.map_axes(stretch)) > 0
        self.stretch = {'uniform': uniform,
                        'tanh_mid': partial(tanh_mid, params=parameters.alpha)}
