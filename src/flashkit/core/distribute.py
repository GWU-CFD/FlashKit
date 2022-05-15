"""Tools for managment of distributing a collection of tasks across workers."""

# type annotations
from __future__ import annotations
from typing import Optional, Sequence

# system libraries
from enum import Enum, EnumMeta
import logging

# internal libraries
from . import parallel
from .error import ParallelError
from .tools import first_true, first_until, pairwise

# external libraries
import numpy

logger = logging.getLogger(__name__)

# define library (public) interface
__all__ = ['Index', ]

def create_directional_enum(*, name: str, dimension: int) -> EnumMeta:
    """Enumeration factory function for creating (directional) paired enum types."""
    pairs = lambda cls: (pair for pair in pairwise(cls))
    enum = Enum(name, {f'A{int(index / 2) + 1}{"HIGH" if index % 2 else "LOW"}': index + 1 for index in range(2 * dimension)})
    setattr(enum, 'pairs', classmethod(pairs))
    return enum

class Index:
    """Support class for parallel process distribution; based on a n-dimensional layout of m-dimensional blocks (or tasks)."""
    # local (all processes have different data)
    high: int
    low: int
    size: int
    range: range
    rank: int

    # global (all processess have same data)
    _directions: EnumMeta
    _edges: EnumMeta
    _layout: Sequence[int]
    _mdim: int
    _ndim: int
    _ranges: dict[int, range]
    _size: int
    _tasks: int

    def __init__(self, *, dimension: int, high: int, layout: Sequence[int], low: int, tasks: int):
        self.high = high
        self.low = low
        self.size = high - low + 1
        self.range = range(low, high + 1)
        self.rank = parallel.rank
        self._directions = create_directional_enum(name='Direction', dimension=len(layout))
        self._edges = create_directional_enum(name='Edge', dimension=dimension)
        self._layout = layout
        self._mdim = dimension
        self._ndim = first_until(layout, lambda n: n == 1)
        self._ranges = {parallel.rank: self.range} if parallel.is_serial() else {k: v for k, v in parallel.COMM_WORLD.allgather((parallel.rank, self.range))}
        self._size = parallel.size
        self._tasks = tasks

    def _invalid_task(self, task: Optional[int]) -> bool:
        """Determine whether a given task is valid for the index."""
        return task is None or not 0 <= task < self._tasks

    def _invalid_where(self, where: Sequence[int]) -> bool:
        """Determine whether the location is valid for the layout."""
        return not all(0 <= local < extent for local, extent in zip(where, self._layout))

    @classmethod
    def from_simple(cls, *, dimension: int = 2, layout: Optional[Sequence[int]] = None, tasks: int = 1):
        """Simple even distribution or processes across communicator."""
        rank: int = parallel.rank # type: ignore
        size: int = parallel.size # type: ignore
        average, residual  = divmod(tasks, size)
        low   =  rank      * (average + 1)     if rank < residual else residual * (average + 1) + (rank - residual    ) * average
        high  = (rank + 1) * (average + 1) - 1 if rank < residual else residual * (average + 1) + (rank - residual + 1) * average - 1
        if layout is None:
            layout = [tasks, ]
        try:
            assert(int(numpy.prod(layout)) == tasks)
            assert((high - low + 1) == (average + 1 if rank < residual else average))
            assert(tasks >= size)
            #assert(dimension >= len(layout))
        except AssertionError:
            raise ParallelError('Could not construct a valid local range of tasks!')
        logger.debug(f'Parallel -- Created a simple distribution of tasks.')
        return cls(dimension=dimension, high=high, layout=layout, low=low, tasks=tasks)

    def get_slices(self, *, task: int, face: EnumMeta, reverse: bool = False) -> tuple[slice, ...]:
        """Return the proper tuple of slices for a boundary face of task data (e.g., data[task, ...])"""
        which = (lambda i: i - 1) if reverse else (lambda i: -i) 
        return (task - self.low, ) + tuple(slice(None) if face not in pair else which(pair.index(face)) for pair in self._edges.pairs())[::-1]

    def get_directions(self, *, pairs: bool = False) -> Union[EnumMeta, Tuple[Tuple[EnumMeta, EnumMeta], ...]]:
        """Return the enumaration of (layout) directions used tasks in the index (e.g., for use in neighbor method)."""
        if not pairs:
            return self._directions
        return tuple(pair for pair in self._directions.pairs())

    def get_edges(self, *, pairs: bool = False) -> Union[EnumMeta, Tuple[Tuple[EnumMeta, EnumMeta], ...]]:
        """Return the enumeration of (geometric) edges used by tasks in the index (e.g., for use in get_slices method)."""
        if not pairs: 
            return self._edges
        return tuple(pair for pair in self._edges.pairs())

    def neighbor(self, *, task: Optional[int], which: EnumMeta, reverse: bool = False) -> Optional[int]:
        """Provide the neighbor of a task in which direction."""
        here = self.where(task)
        if here is None:
            return None
        where = list(here)
        shift = 1 if not reverse else -1
        for axis, (low, high) in enumerate(self._directions.pairs()):
            if which == low:
                where[axis] -= shift
                break
            elif which == high:
                where[axis] += shift
                break
        return self.task(where)

    def task(self, where: Sequence[int]) -> Optional[int]:
        """Provide the task given the location of where it exists within the layout of all tasks."""
        if self._invalid_where(where):
            return None
        return sum(local * int(numpy.prod(self._layout[:axis], initial=1)) for axis, local in enumerate(where))

    def where(self, task: Optional[int]) -> Optional[tuple[int, ...]]:
        """Provide the location of where the task exists within the layout of all tasks."""
        if self._invalid_task(task):
            return None
        return tuple(int(task / numpy.prod(self._layout[:axis], initial=1)) % extent for axis, extent in enumerate(self._layout))          

    @property
    def where_all(self) -> list[tuple[int, ...]]:
        """Provide the locations (i.e., where) for all of the local tasks."""
        return [self.where(n) for n in self.range]

    def what(self, task: int) -> list[str]:
        """Provide the directional context of the task within the layout (e.g., the left, front task); for ndim <= 3."""
        if self._invalid_task(task):
            raise ParallelError('Provided task does not exist in any index!')
        where = self.where(task)
        what = []
        for here, extent, (low, high) in zip(where, self._layout, self._directions.pairs()):
            if here == 0:
                what.append(low)
            if here == extent - 1:
                what.append(high)
        return what

    @property
    def what_all(self) -> list[tuple[int, ...]]:
        """Provide the locations (i.e., what) for all of the local tasks."""
        return [self.what(n) for n in self.range]

    def who(self, task: Optional[int]) -> Optional[int]:
        """Provide the index (i.e., the mpi rank) who owns the task."""
        if self._invalid_task(task):
            return None
        return first_true(self._ranges.items(), lambda item: item[1].start <= task < item[1].stop, (None, ))[0]
        
