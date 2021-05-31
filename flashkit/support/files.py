"""Support methods provided for the file io (e.g., parallel vice serial or mpio support)."""

#type annotations
from __future__ import annotations

# internal libraries
from ..core import parallel
from ..core.error import LibraryError
from .types import D, N

# external libraries
import h5py # type: ignore

# define public interface
__all__ = ['H5Manager', ]


class H5Manager(h5py.File):
    """Context Manager for simple reading and writing of hdf5 files"""
    
    def __init__(self, filename: str, mode: str = 'r', *, clean: bool = False):
        self.filename = filename
        self.mode = mode
        self.clean = clean
        self.serial = parallel.is_serial()
        self.supported = 'mpio' in h5py.registered_drivers()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def close(self) -> None:
        """Ensures proper closing of hdf5 file based on runtime enviornment."""
        if any((self.serial, self.supported, parallel.is_root())):
            self.h5file.close()

    def open(self) -> None:
        """Ensures proper opening of hdf5 file based on runtime enviornment."""
        if self.clean and os.path.exists(self.filename) and parallel.is_root():
            os.remove(self.filename)

        if not self.serial and self.supported:
            self.h5file = h5py.File(self.filename, driver='mpio', comm=parallel.COMM_WORLD)

        elif parallel.is_root():
            self.h5file = h5py.File(self.filename, self.mode)

        else:
            pass

    def read(self, dataset: str) -> D:
        """Retrieve a hdf5 dataset object."""
        if any((self.serial, self.supported, parallel.is_root())):
            return self.read_unsafe(dataset)

    def read_unsafe(self, dataset: str) -> D:
        """Retrieve a hdf5 dataset object; UNSAFE, should wrap in parallel.squash/single."""
        return self.h5file[dataset]

    def write(self, dataset: str, data: N, *, shape: tuple = None, index: parallel.Index = None):
        """Ensure proper creating and writing of hdf5 dataset based on runtime enviornment."""
        
        # write hdf5 file serially
        if self.serial:
            self.h5file.create_dataset(dataset, data=data)
            return

        try:
            assert(index is not None and shape is not None)
        except AssertionError:
            raise LibraryError('Index object and shape are required!')

        # write hdf5 file with parallel support
        if not self.serial and self.supported:
            dset = self.h5file.create_dataset(dataset, shape, dtype=data.dtype)
            dset[index.low:index.high+1] = data
            return

        # write hdf5 file without parallel support 
        if parallel.is_root():
            dset = self.h5file.create_dataset(dataset, shape, dtype=data.dtype)
            
        for process in range(index.size):
            if process == parallel.rank and parallel.is_root():
                dset[index.low:index.high+1] = data

            if process == parallel.rank and not parallel.is_root():
                parallel.COMM_WORLD.Send(data, dest=parallel.ROOT, tag=process)
                parallel.COMM_WORLD.send((index.low, index.high), dest=parallel.ROOT, tag=process+index.size)

            if process != parallel.rank and parallel.is_root():
                parallel.COMM_WORLD.Recv(data, source=process, tag=process)
                low, high = parallel.COMM_WORLD.recv(source=process, tag=process+index.size)
                dset[low:high+1] = data

