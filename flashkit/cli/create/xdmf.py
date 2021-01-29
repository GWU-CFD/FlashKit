"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import List, Optional

# internal libraries
from ...core.create_xdmf_file import create_xdmf_file

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
-b, --low           Begining number for timeseries hdf5 files; defaults to 0.
-e, --high          Ending number for timeseries hdf5 files; defaults to 0.
-s, --skip          Number of files to skip for timeseries hdf5 files; defaults to 1.
-f, --files         List of file numbers [1,2,3,5,7,9] for timeseries.
-p, --path          Path to timeseries hdf5 simulation output files; defaults to cwd.
-o, --out           Output XDMF file name follower; defaults to no footer.
-i, --plot          Plot/Checkpoint file(s) name follower; defaults to '_hdf5_plt_cnt_'.
-g, --grid          Grid file(s) name follower; defaults to '_hdf5_grd_'.
    --help          Show this message and exit.\
"""

IntListType = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 

class XdmfCreateApp(Application):
    """Application class for create xdmf command."""

    interface = Interface(PROGRAM, USAGE, HELP)

    basename: str = None
    interface.add_argument('basename')

    low: int = 0
    interface.add_argument('-b', '--low', type=int, default=low) 

    high: int = 0
    interface.add_argument('-e', '--high', type=int, default=high) 

    skip: int = 1
    interface.add_argument('-s', '--skip', type=int, default=skip) 

    files: Optional[List[int]] = None
    interface.add_argument('-f', '--files', type=IntListType, default=files)

    path: str = ''
    interface.add_argument('-p', '--path', default=path)

    output: str = ''
    interface.add_argument('-o', '--out', default=output)

    plot: str = '_hdf5_plt_cnt_'
    interface.add_argument('-i', '--plot', default=plot)

    grid: str = '_hdf5_grd_'
    interface.add_argument('-g', '--grid', default=grid)

    def run(self) -> None:
        """Buisness logic for 'create xdmf'."""
        
        # Arrange a list of files to process
        if self.files is None:
            self.high = self.high + 1
            self.files = range(self.low, self.high, self.skip)
        else:
            pass

        # Create xdmf file using core library
        print(f'\nCreating xdmf file ...')
        create_xdmf_file(files=self.files, basename=self.basename, path=self.path, 
                         filename=self.output, plotname=self.plot, gridname=self.grid)






