"""Simple tools that support library functions and elsewhere."""

# type annotations
from __future__ import annotations
from typing import Any, Iterator, Optional, Union
from collections.abc import MutableMapping

# standard libraries
import logging
from contextlib import contextmanager
from functools import reduce
from os import chdir
from pathlib import Path

logger = logging.getLogger(__name__)

# define library (public) interface
__all__ = ['change_directory, first_true', 'is_ipython', 'read_a_leaf', ]

@contextmanager
def change_directory(path: Union[Path, str]) -> Iterator[None]:
    """Changes working directory and returns to previous on exit."""
    previous = Path.cwd()
    chdir(Path(path).expanduser().resolve(strict=True))
    logger.debug(f'core -- Working dir changed to: {path}')
    try:
        yield
    finally:
        chdir(previous)
        logger.debug(f'core -- Returned back to dir: {previous}')

def first_true(iterable, predictor):
    return next(filter(predictor, iterable))

def is_ipython() -> bool:
    """Determine if in interactive session."""
    try: 
        get_ipython() # type: ignore
        return True
    except:
        return False

def read_a_leaf(stem: list[str], tree: MutableMapping[str, Any]) -> Optional[Any]:
    """Read the leaf at the end of the stem on the treee."""
    try:
        return reduce(lambda branch, leaf: branch[leaf], stem, tree)
    except KeyError:
        return None
