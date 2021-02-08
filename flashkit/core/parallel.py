"""Tools for management of parallel execution support in the FlashKit library.""" 

# type annotations
from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING

# system libraries
import sys
import os
import pkg_resources
from functools import wraps

# internal libraries
from ..resources import CONFIG

# external libraries
import psutil

if TYPE_CHECKING:
    from types import ModuleType

# default constants
MPICMDS = CONFIG['core']['parallel']['commands']
MPIDIST = CONFIG['core']['parallel']['distribution']
KEYWORD = CONFIG['core']['parallel']['keyword']

class ParallelError(Exception):
    pass

def assertion(method: str, message: str):
    """Usefull decorater to implement supported assertions."""
    def asserter(function):
        @wraps(function)
        def asserted(cls):
            try:
                assert(getattr(cls, method)())
            except AssertionError as error:
                raise ParallelError(message) from error
        return asserted
    return asserter

class Parallel:
    _MPI: ModuleType = None

    @classmethod
    @assertion('is_loaded', 'Python MPI interface appears unloaded; asserted loaded!')
    def assert_loaded(cls) -> None:
        pass

    @classmethod
    @assertion('is_parallel', 'Enviornment appears serial; asserted parallel!')
    def assert_parallel(cls) -> None:
        pass

    @assertion('is_registered', 'Unable to access python MPI interface; module may not be loaded!')
    def assert_registered(cls) -> None:
        pass

    @classmethod
    @assertion('is_serial', 'Enviornment appears parallel; asserted serial!')
    def assert_serial(cls) -> None:
        pass

    @classmethod
    @assertion('is_supported', 'Python MPI interface unsupported; asserted supported!')
    def assert_supported(cls) -> None:
        pass

    @classmethod
    @assertion('is_unloaded', 'Python MPI interface appears loaded; asserted unloaded!')
    def assert_unloaded(cls) -> None:
        pass

    @classmethod
    def is_loaded(cls) -> bool:
        """Identify whether the python MPI interface is already loaded."""
        return MPIDIST in sys.modules

    @classmethod
    def is_parallel(cls) -> bool:
        """Attempt to identify if the python runtime was executed in parallel."""
        return psutil.Process(os.getppid()).name() in MPICMDS

    @classmethod
    def is_registered(cls) -> bool:
        """Identify if the python MPI interface is accessable from Parallel class instances."""
        return cls._MPI is not None 

    @classmethod
    def is_root(cls) -> bool:
        """Determine if execution path is on the root process; true if serial execution."""
        if cls.is_serial():
            return True
        cls.load()
        return cls._MPI.COMM_WORLD.Get_rank() == 0

    @classmethod
    def is_lower(cls, limit: int) -> bool:
        """Determine if execution path is on a process within the processor limit; true if serial execution."""
        if cls.is_serial():
            return True
        cls.load()
        return cls._MPI.COMM_WORLD.Get_rank() < limit

    @classmethod
    def is_serial(cls) -> bool:
        """Attemt to identify whether the python runtime was executed serially."""
        return not cls.is_parallel()

    @classmethod
    def is_supported(cls) -> bool:
        """Identify if the python MPI interface is provided in the enviornment."""
        try:
            pkg_resources.get_distribution(MPIDIST)
            return True
        except pkg_resources.DistributionNotFound:
            return False

    @classmethod
    def is_unloaded(cls) -> bool:
        """Identify if the python MPI interface is not loaded."""
        return not cls.is_loaded()

    @classmethod
    def load(cls) -> None:
        """Attemt to load Python MPI interface; will throw if unsupported and will load even if in serial enviornment."""
        if not cls.is_registered(): 
            cls.assert_supported()
            logged = cls.is_unloaded():
            from mpi4py import MPI
            cls._MPI = MPI
            if logged and MPI.COMM_WORLD.Get_rank == 0:
                print(f'Loaded Python MPI interface, using the {MPIDIST} library.')

    @property
    def MPI(self) -> ModuleType:
        """Retrive the python MPI interface; will throw if unsupported."""
        self.load()
        return self._MPI

    @property
    def COMM_WORLD(self) -> ANY:
        """Retrive World communicator from python MPI interface; will throw if unsupported."""
        return self.MPI.COMM_WORLD

    @property
    def size(self) -> int:
        """Retrive number of parallel processes; does not load python MPI interface if serial."""
        if self.is_parallel():
            return self.COMM_WORLD.Get_size()
        else:
            return 1

    @property
    def rank(self) -> int:
        """Retrive rank of execution process (root if serial); does not load pythin MPI interface if serial."""
        if self.is_parallel():
            return self.COMM_WORLD.Get_rank()
        else:
            return 0

def guard(function):
    """Decorator which assures that neither the python MPI interface is loaded or the python runtime is 
    executed in parallel; this should be used when it is unsafe to run in a parallel enviornment."""
    @warps(function)
    def guarded(*args, **kwargs):
        Parallel.assert_unloaded()
        Parallel.assert_serial()
        return function(*args, **kwargs)
    return guarded

def guarantee(*, strict: bool = False):
    """Decorator which assures that the python MPI interface is loaded prior to the call, and parallel if strict; 
    this should be used in cases were the wrapped function uses the provided infrastructure and also requires 
    access to the underlying MPI object or communicators. If only rank and size are needed should consider using 
    just the support decorator instead, as decorated fuction can likely be run in either parallel or serial naively."""
    def guaranteer(function):
        @wraps(function)
        def guaranteed(*args, **kwargs):
            Parallel.load()
            if strict:
                Parallel.assert_parallel()
            return function(*args, **kwargs)
        return guaranteed
    return guaranteer

def limit(number: int):
    """Decorator which assures that only processes less than the limit execute the decorated funtion; 
    this should be used when it is acceptable to run in a parallel enviornment but is unsafe for more 
    than limit processes to run the function. Decorator will throw if enviornment is parallel
    and python MPI interface unsupported."""
    def limiter(function):
        @wraps(function)
        def limited(*args, **kwargs):
            if Parallel.is_lower(number):
                return function(*args, **kwargs)
            else:
                return None
        return limited
    return limiter

def safe(function):
    """Decorator which passes straight through to decorated function; this should be used
    in cases were the wrapped fuction does not use the provided infrastructure but is
    safe (and sensical) to call in both parallel and serial enviornments."""
    @wraps(function)
    def safed(*args, **kwargs):
        return function(*args, **kwargs)
    return safed

def squash(function):
    """Decorator which passess instance of the Parallel Class, while assuring that only the 
    root processes executes the decorated funtion; this should be used when it is acceptable to
    run in a parallel enviornment but is unsafe for processes other than root to run the function.
    Decorator will throw if enviornment is parallel and python MPI interface unsupported."""
    @wraps(function)
    def squashed(*args, **kwargs):
        if Parallel.is_root():
            return function(*args, **kwargs)
        else:
            return None
    return squashed

def support(function):
    """Decorator which passes instance of the Parallel Class; this should be used
    in cases were the wrapped fuction uses the provided infrastructure and supports
    both parallel and serial execution. Does not guarantee MPI is loaded during call."""
    @wraps(function)
    def supported(*args, **kwargs):
        return function(*args, **kwargs, **{KEYWORD: Parallel()})
    return supported
