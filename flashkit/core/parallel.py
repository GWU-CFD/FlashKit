"""Tools for management of parallel execution support in the FlashKit library.""" 

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# system libraries
import sys
import os
import pkg_resources
from functools import wraps

# internal libraries
from ..resources import CONFIG

# external libraries
import psutil

# static analysis
if TYPE_CHECKING:
    from types import ModuleType
    Intracomm = TypeVar('Intracomm', bound = Any)
    F = TypeVar('F', bound = Callable[..., Any])
    D = TypeVar('D', bound = Callable[[F], F])

# module access and module level @property(s)
SELF = sys.modules[__name__]
PROPERTIES = ('MPI', 'COMM_WORLD', 'rank', 'size', ) 

# define public interface
__all__ = list(PROPERTIES) + [
        'ParallelError', 'guard', 'guarantee', 'limit', 'safe', 'squash', 'single',
        'is_loaded', 'is_lower', 'is_parallel', 'is_root', 'is_serial', 'is_supported', ]

# default constants
MPICMDS = CONFIG['core']['parallel']['commands']
MPIDIST = CONFIG['core']['parallel']['distribution']
ROOT = CONFIG['core']['parallel']['root']
SIZE = CONFIG['core']['parallel']['size']

# python MPI interface access member
_MPI: ModuleType = None

def __getattr__(name: str) -> Any:
    """Provide module level @property behavior."""
    if name in PROPERTIES: return globals()[get_property(name)]()
    raise AttributeError(f'module {__name__} has no attribute {name}')

class ParallelError(Exception):
    """Available for handling errors raised by parallel module"""

def assertion(method: str, message: str) -> D:
    """Usefull decorater factory to implement supported assertions."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper() -> None:
            try:
                assert(getattr(SELF, method)())
            except AssertionError as error:
                raise ParallelError(message) from error
        return wrapper
    return decorator

def inject_property(name: str) -> D:
    """Usefull decorator factory to provide access to module properties."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args, **kwargs) -> Any:
            return function(getattr(SELF, get_property(name)), *args, **kwargs)
        return wrapper
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
    return psutil.Process(os.getppid()).name() in MPICMDS

@inject_property('rank')
def is_root(rank: F) -> bool:
    """Determine if local execution process is the root process; true is serial."""
    return rank() == ROOT

def is_registered() -> bool:
    """Identify if the python MPI interface is accessable from Parallel class instances."""
    return _MPI is not None 

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
    from mpi4py import MPI
    SELF._MPI = MPI
    if first and MPI.COMM_WORLD.Get_rank() == 0:
        print(f'\nLoaded Python MPI interface, using the {MPIDIST} library.\n')

@inject_property('MPI')
def property_COMM_WORLD(mpi: F) -> Intracomm:
    """MPI python interface world communicator."""
    return mpi().COMM_WORLD

def property_MPI() -> ModuleType:
    """MPI python interface access handle."""
    load()
    return SELF._MPI

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
    @warps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        assert_unloaded()
        assert_serial()
        return function(*args, **kwargs)
    return wrapper

def guarantee(*, strict: bool = False) -> D:
    """Decorator which assures that the python MPI interface is loaded prior to the call, and parallel if strict; 
    this should be used in cases were the wrapped function uses the provided infrastructure and also requires 
    access to the underlying MPI object or communicators. If only rank and size are needed should consider using 
    just the support decorator instead, as decorated fuction can likely be run in either parallel or serial naively."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if strict: assert_parallel()
            load()
            return function(*args, **kwargs)
        return wrapper
    return decorator

def limit(number: int) -> D:
    """Decorator which assures that only processes less than the limit execute the decorated funtion; 
    this should be used when it is acceptable to run in a parallel enviornment but is unsafe for more 
    than limit processes to run the function. Decorator will throw if enviornment is parallel
    and python MPI interface unsupported."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_lower(number): return 
            return function(*args, **kwargs)
        return wrapper
    return decorator

def safe(function: F) -> F:
    """Decorator which passes straight through to decorated function; this should be used
    in cases were the wrapped fuction does not use the provided infrastructure but is
    safe (and sensical) to call in both parallel and serial enviornments."""
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return function(*args, **kwargs)
    return wrapper

def squash(function: F) -> F:
    """Decorator which assures that only the root processes executes the decorated funtion; this should be used 
    when it is acceptable to run in a parallel enviornment but is unsafe for processes other than root to run the function.
    Decorator will throw if enviornment is parallel and python MPI interface unsupported."""
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_root(): return
        return function(*args, **kwargs)
    return wrapper

def single(function: F) -> F:
    """Decorator like squash, but joins the parallel execution back together by broadcasting result of root."""
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if is_serial(): return function(*args, **kwargs)
        load()
        if is_root():
            result = function(*args, **kwargs)
        else:
            result = None
        return SELF._MPI.COMM_WORLD.bcast(result, root=ROOT)
    return wrapper
