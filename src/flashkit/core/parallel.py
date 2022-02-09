"""Tools for management of parallel execution support in the FlashKit library.""" 

# type annotations
from __future__ import annotations
from typing import cast, TYPE_CHECKING

# system libraries
from enum import Enum, EnumMeta
import logging
import os
import sys
import pkg_resources
from functools import wraps

# internal libraries
from .error import ParallelError
from .tools import first_true, first_until, pairwise
from ..resources import CONFIG

# external libraries
import numpy
import psutil # type: ignore

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Sequence, TypeVar
    from types import ModuleType
    Intracomm = TypeVar('Intracomm', bound=Any)
    F = TypeVar('F', bound = Callable[..., Any])
    D = Callable[[F], F]

# deal w/ runtime cast
else:
    F = None

logger = logging.getLogger(__name__)

# module access and module level @property(s)
this = sys.modules[__name__]
PROPERTIES = ('MPI', 'COMM_WORLD', 'rank', 'size', ) 

# define library (public) interface
__all__ = list(PROPERTIES) + ['Index', 
        'guard', 'guarantee', 'limit', 'safe', 'squash', 'single',
        'is_loaded', 'is_lower', 'is_parallel', 'is_root', 'is_serial', 'is_supported', ]

# default constants
MPICMDS = CONFIG['core']['parallel']['commands']
MPIDIST = CONFIG['core']['parallel']['distribution']
ROOT = CONFIG['core']['parallel']['root']
SIZE = CONFIG['core']['parallel']['size']

# python MPI interface access member
_MPI: Optional[ModuleType] = None

# internal member for forced parallel
_parallel: Optional[bool] = None

def __getattr__(name: str) -> Any:
    """Provide module level @property behavior."""
    if name in PROPERTIES: return globals()[get_property(name)]()
    raise AttributeError(f'module {__name__} has no attribute {name}')

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
    _block: EnumMeta
    _boundary: EnumMeta
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
        self.rank = this.rank
        self._block = create_directional_enum('Block', dimension=dimension)
        self._boundary = create_directional_enum('Boundary', dimension=len(layout))
        self._layout = layout
        self._mdim = dimension
        self._ndim = first_until(layout, lambda n: n == 1)
        self._ranges = {this.rank: self.range} if this.is_serial() else {k: v for k, v in this.COMM_WORLD.allgather((this.rank, self.range))}
        self._size = this.size
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
        rank: int = this.rank # type: ignore
        size: int = this.size # type: ignore
        average, residual  = divmod(tasks, size)
        low   =  rank      * (average + 1)     if rank < residual else residual * (average + 1) + (rank - residual    ) * average
        high  = (rank + 1) * (average + 1) - 1 if rank < residual else residual * (average + 1) + (rank - residual + 1) * average - 1
        if layout is None:
            layout = [tasks, ]
        try:
            assert(int(numpy.prod(layout)) == tasks)
            assert((high - low + 1) == (average + 1 if rank < residual else average))
            assert(tasks >= size)
            assert(dimension >= len(layout))
        except AssertionError:
            raise ParallelError('Could not construct a valid local range of tasks!')
        logger.debug(f'Parallel -- Created a simple distribution of tasks.')
        return cls(dimension=dimension, high=high, layout=layout, low=low, tasks=tasks)

    def get_slice(self, *, task: int, bound: EnumMeta, reverse: bool = False) -> slice:
        """Return the proper slice for a direction boundary into block data (e.g., data[task, left, ...])"""
        which = (lambda i: i - 1) if reverse else (lambda i: -i) 
        return (slice(None) if bound not in pair else slice(which(pair.index(bound))) for pair in self._block.pairs())

    def neighbor(self, *, task: Optional[int], which: EnumMeta, reverse: bool = False) -> Optional[int]:
        """Provide the neighbor of a task in which direction."""
        here = self.where(task)
        if here is None:
            return None
        where = list(here)
        shift = 1 if not reverse else -1
        for axis, (low, high) in enumerate(self._boundary.pairs()):
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
        """Provide the boundary context of the task within the layout (e.g., the left, front task); for ndim <= 3."""
        if self._invalid_task(task):
            raise ParallelError('Provided task does not exist in any index!')
        where = self.where(task)
        ndim = first_until(self._layout, lambda n: n == 1)
        what = []
        for dist, bound, (low, high) in zip(where, self._layout[:ndim], self._boundary.pairs()):
            if dist == 0:
                what.append(low)
            if dist == bound - 1:
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
        
def assertion(method: str, message: str) -> D:
    """Usefull decorater factory to implement supported assertions."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper():
            try:
                assert(getattr(this, method)())
            except AssertionError as error:
                raise ParallelError(message) from error
        return cast(F, wrapper)
    return decorator

def inject_property(name: str) -> D:
    """Usefull decorator factory to provide access to module properties."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args, **kwargs):
            return function(getattr(this, get_property(name)), *args, **kwargs)
        return cast(F, wrapper)
    return decorator

@assertion('is_loaded', 'Python MPI interface appears unloaded; asserted loaded!')
def assert_loaded() -> None:
    pass

@assertion('is_parallel', 'Enviornment appears serial; asserted parallel!')
def assert_parallel() -> None:
    pass

@assertion('is_registered', 'Unable to access python MPI interface; module may not be loaded!')
def assert_registered() -> None:
    pass

@assertion('is_serial', 'Enviornment appears parallel; asserted serial!')
def assert_serial() -> None:
    pass

@assertion('is_supported', 'Python MPI interface unsupported; asserted supported!')
def assert_supported() -> None:
    pass

@assertion('is_unloaded', 'Python MPI interface appears loaded; asserted unloaded!')
def assert_unloaded() -> None:
    pass

@inject_property('COMM_WORLD')
def barrier(comm: Intracomm) -> None:
    """MPI python interface world communicator."""
    if is_parallel(): comm().Barrier()

def force_parallel(state: bool = True) -> None:
    """Force the assumption of a parallel or serial state."""
    this._parallel = state # type: ignore
    logger.debug('Force -- Parallel Enviornment!')

def get_property(name: str) -> str:
    """Provide lookup support for module properties."""
    return f'property_{name}'

def is_loaded() -> bool:
    """Identify whether the python MPI interface is already loaded."""
    return MPIDIST in sys.modules

@inject_property('rank')
def is_lower(rank: F, limit: int) -> bool:
    """Determine if execution path is on a process within the processor limit; true if serial execution."""
    return rank() < limit

def is_parallel() -> bool:
    """Attempt to identify if the python runtime was executed in parallel."""
    if this._parallel is not None: return this._parallel # type: ignore
    process = psutil.Process(os.getppid())
    return process.name() in MPICMDS or any(command in MPICMDS for command in process.cmdline())

@inject_property('rank')
def is_root(rank: F) -> bool:
    """Determine if local execution process is the root process; true is serial."""
    return rank() == ROOT

def is_registered() -> bool:
    """Identify if the python MPI interface is accessable from Parallel class instances."""
    return this._MPI is not None # type: ignore

def is_serial() -> bool:
    """Attemt to identify whether the python runtime was executed serially."""
    return not is_parallel()

def is_supported() -> bool:
    """Identify if the python MPI interface is provided in the enviornment."""
    try:
        pkg_resources.get_distribution(MPIDIST)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def is_unloaded() -> bool:
    """Identify if the python MPI interface is not loaded."""
    return not is_loaded()

def load() -> None:
    """Attemt to load Python MPI interface; will throw if unsupported and will load even if in serial enviornment."""
    if is_registered(): return 
    assert_supported()
    first = is_unloaded()
    from mpi4py import MPI # type: ignore
    this._MPI = MPI # type: ignore
    if first and MPI.COMM_WORLD.Get_rank() == 0:
        logger.info(f'\nLoaded Python MPI interface, using the {MPIDIST} library.\n')

@inject_property('MPI')
def property_COMM_WORLD(mpi: F) -> Intracomm:
    """MPI python interface world communicator."""
    return mpi().COMM_WORLD

def property_MPI() -> ModuleType:
    """MPI python interface access handle."""
    load()
    assert this._MPI is not None # type: ignore
    return this._MPI # type: ignore

@inject_property('COMM_WORLD')
def property_rank(comm: F) -> int:
    """Rank of local execution process."""
    if is_parallel(): return comm().Get_rank()
    return ROOT

@inject_property('COMM_WORLD')
def property_size(comm: F) -> int:
    """Number of parallel execution processes (serial defined as {SIZE})."""
    if is_parallel(): return comm().Get_size()
    return SIZE

def guard(function: F) -> F:
    """Decorator which assures that neither the python MPI interface is loaded or the python runtime is 
    executed in parallel; this should be used when it is unsafe to run in a parallel enviornment."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        assert_unloaded()
        assert_serial()
        logger.debug(f'Parallel -- Guarded (Guard) a call into <{function.__name__}>.')
        return function(*args, **kwargs)
    return cast(F, wrapper)

def guarantee(*, strict: bool = False) -> D:
    """Decorator which assures that the python MPI interface is loaded prior to the call, and parallel if strict; 
    this should be used in cases were the wrapped function uses the provided infrastructure and also requires 
    access to the underlying MPI object or communicators. If only rank and size are needed should consider using 
    just the support decorator instead, as decorated fuction can likely be run in either parallel or serial naively."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args, **kwargs):
            if strict: assert_parallel()
            load()
            logger.debug(f'Parallel -- Guarded (Guarantee) a call into <{function.__name__}>.')
            return function(*args, **kwargs)
        return cast(F, wrapper)
    return decorator

def limit(number: int) -> D:
    """Decorator which assures that only processes less than the limit execute the decorated funtion; 
    this should be used when it is acceptable to run in a parallel enviornment but is unsafe for more 
    than limit processes to run the function. Decorator will throw if enviornment is parallel
    and python MPI interface unsupported."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args, **kwargs):
            if not is_lower(number): return 
            logger.debug(f'Parallel -- Guarded (limit) a call into <{function.__name__}>.')
            return function(*args, **kwargs)
        return cast(F, wrapper)
    return decorator

def many(number: Optional[int] = None, *, root: bool = True) -> D:
    """Decorator like limit, but joins the parallel execution back together by broadcasting result of each process;
    this should be used when either (root == False) each process needs to know what the other returned,
    or many processes are needed for the decorated function but only the result or root is desired on return."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args, **kwargs):
            if is_serial(): return function(*args, **kwargs)
            load()
            if number is None or is_lower(number):
                logger.debug(f'Parallel -- Guarded (many) a call into <{function.__name__}>.')
                result = function(*args, **kwargs)
            else:
                result = None
            if root: return this._MPI.COMM_WORLD.bcast(result, root=ROOT)
            logger.debug(f'Parallel -- Gathering (many) results of a call into <{function.__name__}>.')
            return this._MPI.COMM_WORLD.allgather(result)
        return cast(F, wrapper)
    return decorator

def safe(function: F) -> F:
    """Decorator which passes straight through to decorated function; this should be used
    in cases were the wrapped fuction does not use the provided infrastructure but is
    safe (and sensical) to call in both parallel and serial enviornments."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        logger.debug(f'Parallel -- Passing (safe) through the call into <{function.__name__}>.')
        return function(*args, **kwargs)
    return cast(F, wrapper)

def squash(function: F) -> F:
    """Decorator which assures that only the root processes executes the decorated funtion; this should be used 
    when it is acceptable to run in a parallel enviornment but is unsafe for processes other than root to run the function.
    Decorator will throw if enviornment is parallel and python MPI interface unsupported."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not is_root(): return
        logger.debug(f'Parallel -- Guarded (squash) the call into <{function.__name__}>.')
        return function(*args, **kwargs)
    return cast(F, wrapper)

def single(function: F) -> F:
    """Decorator like squash, but joins the parallel execution back together by broadcasting result of root."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if is_serial(): return function(*args, **kwargs)
        load()
        if is_root():
            logger.debug(f'Parallel -- Guarded (single) the call into <{function.__name__}>.')
            result = function(*args, **kwargs)
        else:
            result = None
        logger.debug(f'Parallel -- Distributing (single) result of a call into <{function.__name__}>.')
        return this._MPI.COMM_WORLD.bcast(result, root=ROOT)
    return cast(F, wrapper)
