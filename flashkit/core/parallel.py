


# type annotations
from __future__ import annotations
from typing import NamedTuple

# system libraries
import sys
import os
import pkg_resources

# external libraries
import psutil

# defined constants
MPICMDS = {'mpirun', 'mpiexec'}
MPIDIST = 'mpi4py'

class ParallelError(Exception):
    pass

class Parallel:
    __cached: bool = False
    __loaded: bool = False
    __parallel: bool = False
    __supported: bool = False

    @classmethod
    def __is_loaded(cls) -> bool:
        if cls.__cached:
            return cls.__loaded
        return MPIDIST in sys.modules

    @classmethod
    def __is_parallel(cls) -> bool:
        if cls.__cached:
            return cls.__parallel
        return psutil.Process(os.getppid()).name in MPICMDS

    @classmethod
    def __is_supported(cls) -> bool:
        if cls.__cached:
            return cls.__supported
        try:
            pkg_resources.get_distribution(MPIDIST)
            return True
        except pkg_resources.DistributionNotFound as error:
            raise ParallelError(f'Parallel enviornment not available; {MPIDIST} not found!')


    def __init__(self):
        pass

    @property
    def COMM_WORLD(self) -> Any:
        if mpi_loaded():
            return mpi_initialize().COMM_WORLD
        else:
            raise ParallelError('Python MPI interface is not yet intialized!')

    @property
    def size(self) -> int:
        if mpi_loaded():
            return mpi_initialize().COMM_WORLD.Get_size()
        else:
            return 1

    @property
    def rank(self) -> int:
        if mpi_loaded():
            return mpi_initialize().COMM_WORLD.Get_rank()
        else:
            return 0
