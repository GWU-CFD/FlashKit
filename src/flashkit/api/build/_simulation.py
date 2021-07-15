"""Build and compile a FLASH simulation directory."""

# type annotations
from __future__ import annotations
from typing import Any

# standard libraries
import logging
import os
import sys
from pathlib import Path

# internal libraries
from ...core.error import AutoError
from ...core.parallel import safe, single, squash 
from ...core.progress import attach_context
from ...core.stream import Instructions, mail
from ...library.build_simulation import build, make
from ...resources import CONFIG

logger = logging.getLogger(__name__)

# define public interface
__all__ = ['simulation', ]

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""
    
    # ensure arguments provided
    if any(arg not in args for arg in {'simulation', 'directory'}):
        raise AutoError('Both simulation and directory arguments needed!')

    try:
        # resolve proper absolute directory paths
        args['path'] = Path(args['path']).expanduser().resolve(strict=True)
    except FileNotFoundError:
        raise AutoError('Cannot resolve path to FLASH source repository!')
    logger.debug(f'api -- Fully resolved the FLASH source repository.')

    try:
        # format options and validation of user input
        ndim = max(min(3, args['ndim']), 2)
        nxb, nyb, nzb = (args[b] for b in ('nxb', 'nyb', 'nzb'))
        grid = {'paramesh': 'pm4dev', 'uniform': 'ug', 'regular': 'rg'}.get(args['grid'], args['grid'].strip('-+'))
        sub = args['subpath'].rstrip('/')
        sim = args['simulation'].rstrip('/')
        objdir = f"{grid}{args['directory']}_{nxb}_{nyb}" + '' if ndim == 2 else f'_{nzb}'
        python = './setup' if max(min(3, args['python']), 2) == 2 else './setup3'
        flag = args['optimize'].strip('-+')
        parallelIO = '' if 'parallelIO' not in args else ' +parallelIO'
        shortcuts = '' if 'shortcuts' not in args else ' +' + ' +'.join(args['shortcuts'])
        options = '' if 'flags' not in args else ' -' + ' -'.join(args['flags'])
        variables = ' '.join([f'-{name}={value}' for name, value in args.get('variables', {}).items()])
        site = args['site']
    except:
        raise AutoError('Failed to understand and validate input!')
    logger.debug(f'api -- Validated user input and formated options.')

    # create setup command
    args['setup'] = f'{python} {sub}/{sim}/ +{grid} +hdf5{parallelIO}{shortcuts}' \
                    f' -auto -{flag}{options} -objdir={objdir} -site={site}' \
                    f' -{ndim}d -nxb={nxb} -nyb={nyb}{f" -nzb={nzb}" if ndim == 3 else ""}' \
                    f'{variables}'.split()
    args['directory'] = objdir
    logger.debug(f'api -- Constructed setup command.')

    return args

# default constants for handling the argument stream
PACKAGES = {'simulation', 'directory', 'ndim', 'nxb', 'nyb', 'nzb', 'grid', 'python', 'site', 'optimize', 'parallelIO', 
            'shortcuts', 'flags', 'variables', 'subpath', 'path', 'compile', 'jobs', 'build', 'force'}
ROUTE = ('build', 'simulation')
PRIORITY = {'ignore', 'cmdline'}
CRATES = (adapt_arguments, attach_context)
DROPS = {'ignore', 'ndim', 'nxb', 'nyb', 'nzb', 'grid', 'python', 'site', 'optimize', 'parallelIO', 'shortcuts', 
         'flags', 'variables', 'subpath'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

@safe
def simulation(**arguments: Any) -> None:
    """Python application interface for building and compiling FLASH simulation build directories.

    This method creates a FLASH simulation setup command using options and specified defaults
    executes the build in a subprocess to enable the creation of FLASH simulation build directories.
    The build directories can also be compiled (even in parallel; e.g., 'make -j 4'), if desired.

    Keyword Arguments:
        simulation (str):   Specify a simulation directory contained in the FLASH source/Simulation/SimulationMain.
        directory (str):    Specify a build directory basename; will be determined if not provided. 
        ndim (int):         Number of simulation dimensions (i.e., 2 or 3).
        nxb (int):          Number of grid points per block in the i direction.
        nyb (int):          Number of grid points per block in the j direction.
        nzb (int):          Number of grid points per block in the k direction.
        grid (str):         Type of FLASH simulation grid used by the Grid Package (e.g., 'regular').
        python (int):       Python version for the setup script; specifically use either 2 (legacy) or 3 (modern).
        site (str):         Hostname of the machine on which setup is being run; Makefile should be in sites/SITE.
        optimize (str):     Flag (e.g., 'debug') for compilation and linking; using either optimized, debugging, or other. 
        parallelIO (bool):  Use the parallel HDF5 Input/Output library.
        shortcuts (list):   Additional setup shortcuts (example: +rg) which begin with a plus symbol.  
        flags (list):       Additional setup options (example: -auto) which begin with a dash.
        variables (dict):   Additional setup variable pairs (example: -nxb=12) which begin with a dash.
        subpath (str):      Specify a Simulation directory sub-path to SIMULATION within source/Simulation/SimulationMain.
        path (str):         Path to the local FLASH source repository.
        compile (bool):     Compile the FLASH simulation build directory after it is constructed.
        jobs (int):         Number of parallel processes to use when executing the make command.
        build (bool):       Force the building of the simulation directory, even if the directory exists. 
        force (bool):       Force the compilation of the build directory, even if the binary is present. 
        ignore (bool):      Ignore configuration file provided arguments, options, and flags.
    """
    args = process_arguments(**arguments)
    
    force_build = args.pop('build', False)
    force_make = args.pop('force', False)
    comp = args.pop('compile', False)
    jobs = args.pop('jobs')
    setup = args.pop('setup')
    sim = args.pop('simulation')
    cmdline = args.pop('cmdline', False)
    
    build(simulation=sim, force=force_build, setup=setup, **args)
    if comp: make(force=force_make, jobs=jobs, **args)
