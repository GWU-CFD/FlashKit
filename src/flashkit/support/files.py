"""Support methods provided for the file io (e.g., parallel vice serial or mpio support)."""

#type annotations
from __future__ import annotations

# standard libraries
import os

# internal libraries
from ..core import parallel
from ..core.error import LibraryError
from .types import D, N

# external libraries
import h5py # type: ignore

# define public interface
__all__ = ['H5Manager', ]

class H5Manager:
    """Context Manager for simple reading and writing of hdf5 files"""
    
    def __init__(self, filename: str, mode: str = 'r', *, 
                 clean: bool = False, force: bool = False, nofile: bool = False):
        
        self.h5file = None
        self.filename = filename
        self.mode = mode
        
        self.clean = clean
        self.force = mode == 'r' and force
        self.nofile = nofile

        self.serial = parallel.is_serial()
        self.supported = 'mpio' in h5py.registered_drivers()
        self.safe = any((self.supported, self.serial, parallel.is_root(), self.force)) and not nofile

        try:
            assert(mode in {'r', 'r+', 'w', 'w-', 'x', 'a'})
        except AssertionError as error:
            raise LibraryError('Invalid file mode requested!') from error

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def __contains__(self, key):
        if self.h5file is None:
            LibraryError('Hdf5 File has not been opened!')
        return key in self.h5file.keys()

    def close(self) -> None:
        """Ensures proper closing of hdf5 file based on runtime enviornment."""
        if self.safe:
            self.h5file.close()

    def create_dataset(self, dataset: str, *, shape: tuple, dtype: type, force: bool = False) -> None:
        """Ensure proper creation of hdf5 dataset based on runtime enviornment."""
        if self.safe:
            if force or dataset not in self:
                self.h5file.create_dataset(dataset, shape, dtype=dtype)

    def open(self) -> None:
        """Ensures proper opening of hdf5 file based on runtime enviornment."""
        if self.nofile: return

        if self.clean and os.path.exists(self.filename) and parallel.is_root():
            os.remove(self.filename)
        
        if not self.serial and self.supported:
            self.h5file = h5py.File(self.filename, self.mode, driver='mpio', comm=parallel.COMM_WORLD)
        
        elif parallel.is_root() or self.force:
            self.h5file = h5py.File(self.filename, self.mode)
        
        else:
            pass

    def read(self, dataset: str) -> D:
        """Retrieve a hdf5 dataset object."""
        if self.safe: 
            return self.read_unsafe(dataset)

    def read_unsafe(self, dataset: str) -> D:
        """Retrieve a hdf5 dataset object; UNSAFE, should wrap in parallel.squash/single."""
        return self.h5file[dataset]

    def write(self, dataset: str, data: N, *, shape: tuple = None, index: parallel.Index = None) -> None:
        """Ensure proper creating and writing of hdf5 dataset based on runtime enviornment."""
        if self.nofile: return

        # write hdf5 file serially
        if self.serial:
            self.h5file.create_dataset(dataset, data=data)
            return

        if index is None or shape is None:
            raise LibraryError('Index object and shape are required!')

        # write hdf5 file with parallel support
        if self.supported:
            dset = self.h5file.create_dataset(dataset, shape, dtype=data.dtype)
            dset[index.low:index.high+1] = data
            return

        # write hdf5 file without parallel support
        comm = parallel.COMM_WORLD
        if parallel.is_root():
            dset = self.h5file.create_dataset(dataset, shape, dtype=data.dtype)
            
        for process in range(index.size):
            if process == parallel.rank and parallel.is_root():
                dset[index.low:index.high+1] = data

            if process == parallel.rank and not parallel.is_root():
                comm.Send(data, dest=parallel.ROOT, tag=process)
                comm.send((index.low, index.high), dest=parallel.ROOT, tag=process+index.size)

            if process != parallel.rank and parallel.is_root():
                comm.Recv(data, source=process, tag=process)
                low, high = comm.recv(source=process, tag=process+index.size)
                dset[low:high+1] = data

    def write_partial(self, dataset: str, data: N, *, block: int, index: parallel.Index = None) -> None:
        """Ensure proper writing of hdf5 dataset based on runtime enviornment; Must create dataset first."""
        if self.nofile: return

        # write hdf5 file serially or with parallel support
        if self.serial or self.supported:
            self.h5file[dataset][block] = data
            return
        
        if index is None:
            raise LibraryError('Index object is required!')

        # write hdf5 file without parallel support
        comm = parallel.COMM_WORLD
        for process in range(index.size):
            if process == parallel.rank and parallel.is_root():
                self.h5file[dataset][block] = data

            if process == parallel.rank and not parallel.is_root():
                comm.Send(data, dest=parallel.ROOT, tag=process)

            if process != parallel.rank and parallel.is_root():
                comm.Recv(data, source=process, tag=process)
                self.h5file[dataset][block] = data
