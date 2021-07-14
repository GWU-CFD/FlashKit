"""Build and compile a FLASH simulation directory."""

# type annotations
from __future__ import annotations

# standard libraries
import logging
import os
import re
import subprocess
from pathlib import Path

# internal libraries
from ..core.error import LibraryError
from ..core.parallel import squash
from ..core.progress import Bar
from ..core.tools import change_directory
from ..resources import CONFIG

logger = logging.getLogger(__name__)

# define library (public) interface
__all__ = ['build', 'make', ]

# define configuration constants (internal)
BINARY = CONFIG['build']['simulation']['binary']
SUCCESS = CONFIG['build']['simulation']['success']
TIMEOUT = CONFIG['build']['simulation']['timeout']

@squash
def build(*, directory: str, simulation: str, force: bool, path: Path, setup: list[str], context: Bar) -> None:
    """Executes the FLASH build process with the intended options."""
    build = path.joinpath(directory)
    if build.exists() and not force:
        logger.warning(f'The simulation directory {directory} exists!')
        return
    print(f'\n'
          f'------------------------------------------------------------------\n'
          f'Create FLASH Compilation Directory -- {simulation}\n'
          f'------------------------------------------------------------------\n\n'
          f'Using the following FLASH setup command:\n'
          f'----------------------------------------\n'
          f'{" ".join(setup)}\n\n')
    try:
        with context() as progress:
            output = subprocess.run(setup, cwd=path, timeout=TIMEOUT, capture_output=True)
    except subprocess.TimeoutExpired:
        raise LibraryError('Failed to build within alloted time!')
    except subprocess.CalledProcessError as error:
        raise LibraryError(f'Failed build with exit code {error.returncode}!')
    else:
        outform = output.stdout.decode('utf-8')
        logger.debug(outform)
        if not re.search(SUCCESS, outform):
            raise LibraryError('Failed to build simulation directory!')
        logger.info('Successfully built simulation directory')

@squash
def make(*, directory: str, force: bool, jobs: int, path: Path, context: Bar) -> None:
    """Compile the FLASH build directory."""
    build = path.joinpath(directory)
    binary = build.joinpath(BINARY)
    setup = ['make', '-j', str(jobs)]
    if not build.exists():
        logger.info(f'The simulation directory {directory} does not exist!')
        return
    if binary.exists() and not force:
        logger.info(f'The simulation binary already exists!')
        return
    print(f'\n' \
          f'Compile the FLASH setup directory w/ {jobs} cores:\n' \
          f'-----------------------------------------------------\n' \
          f'\n' \
          f'Compiling FLASH code ...\n' \
          f'\n')
    try:
        with context() as progress:
            output = subprocess.run(setup, cwd=build, timeout=TIMEOUT, capture_output=True)
    except subprocess.TimeoutExpired:
        raise LibraryError('Failed to compile within alloted time!')
    except subprocess.CalledProcessError as error:
        raise LibraryError(f'Failed compilation with exit code {error.returncode}!')
    else:
        if not re.search(SUCCESS, output.stdout.decode('utf-8')):
            raise LibraryError('Failed to compile simulation directory!')
        logger.info('Successfully compiled simulation directory')
