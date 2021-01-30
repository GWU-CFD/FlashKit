"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import List, Optional

# internal libraries
from ...lib import create_xdmf

# external libraries
from cmdkit.app import Application
from cmdkit.cli import Interface

PROGRAM = f'flash create xdmf'

USAGE = f"""\
usage: {PROGRAM} BASENAME [[<opt> <arg(s)>]...]
{__doc__}\
"""

HELP = f"""\
{USAGE}

arguments:
BASENAME            Basename for flash simulation
                    (e.g., INS_Rayleigh for files INS_Rayleigh_hdf5_plt_cnt_xxxx)

options:
-b, --low           Begining number for timeseries hdf5 files; defaults to {create_xdmf.LOW}.
-e, --high          Ending number for timeseries hdf5 files; defaults to {create_xdmf.HIGH}.
-s, --skip          Number of files to skip for timeseries hdf5 files; defaults to {create_xdmf.SKIP}.
-f, --files         List of file numbers (e.g., <1,3,5,7,9>) for timeseries.
-p, --path          Path to timeseries hdf5 simulation output files; defaults to cwd.
-o, --out           Output XDMF file name follower; defaults to no footer.
-i, --plot          Plot/Checkpoint file(s) name follower; defaults to '{create_xdmf.PLOT}'.
-g, --grid          Grid file(s) name follower; defaults to '{create_xdmf.GRID}'.
-h, --help          Show this message and exit.\
"""

# Create argpase List custom types
IntListType = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 

# Patch exception message output for this module
def logError(message: str) -> None:
    Application.log_critical(f'\nUnable to create xdmf file!\n{message}')

class XdmfCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)

    basename: str = None
    interface.add_argument('basename')

    low: int = create_xdmf.LOW 
    interface.add_argument('-b', '--low', type=int, default=low) 

    high: int = create_xdmf.HIGH 
    interface.add_argument('-e', '--high', type=int, default=high) 

    skip: int = create_xdmf.SKIP
    interface.add_argument('-s', '--skip', type=int, default=skip) 

    files: Optional[List[int]] = None
    interface.add_argument('-f', '--files', type=IntListType, default=files)

    path: str = create_xdmf.PATH
    interface.add_argument('-p', '--path', default=path)

    output: str = create_xdmf.OUTPUT
    interface.add_argument('-o', '--out', default=output)

    plot: str = create_xdmf.PLOT
    interface.add_argument('-i', '--plot', default=plot)

    grid: str = create_xdmf.GRID
    interface.add_argument('-g', '--grid', default=grid)

    log_critical: Callable[[str], None] = logError 
    log_exception: Callable[[str], None] = logError 

    def run(self) -> None:
        """Buisness logic for creating xdmf from command line."""
        
        # Arrange a list of files to process
        if self.files is None:
            self.high = self.high + 1
            self.files = range(self.low, self.high, self.skip)
        else:
            pass

        # Create xdmf file using core library
        print(f'\nCreating xdmf file ...')
        create_xdmf.file(files=self.files, basename=self.basename, path=self.path, 
                         filename=self.output, plotname=self.plot, gridname=self.grid)
