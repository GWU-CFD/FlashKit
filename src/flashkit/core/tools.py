"""Simple tools that support library functions and elsewhere."""

# type annotations
from __future__ import annotations
from ast import Call
from typing import Any, Callable, Iterator, Iterable, Optional, Union
from collections.abc import MutableMapping

# standard libraries
import logging
from contextlib import contextmanager
from functools import reduce
from os import chdir
from pathlib import Path

logger = logging.getLogger(__name__)

# define library (public) interface
__all__ = ['change_directory, first_true', 'is_ipython', 'read_a_branch', 'read_a_leaf', ]

@contextmanager
def change_directory(path: Union[Path, str]) -> Iterator[None]:
    """Changes working directory and returns to previous on exit."""
    previous = Path.cwd()
    chdir(Path(path).expanduser().resolve(strict=True))
    logger.debug(f'Core -- Working dir changed to: {path}.')
    try:
        yield
    finally:
        chdir(previous)
        logger.debug(f'Core -- Returned back to dir: {previous}.')

def first_true(iterable: Iterable, predictor: Callable, default: Optional[Any] = None) -> Any:
    """Given an iterable, provide the first element where the predicate is true."""
    return next(filter(predictor, iterable), default)

def first_until(iterable: Iterable, predictor: Callable) -> int:
    """Given an iterable, provide the size (i.e., stop index) until the predicate is always true."""
    return len(iterable) - next((index for index, it in enumerate(reversed(iterable)) if not predictor(it)), len(iterable))

def is_ipython() -> bool:
    """Determine if in interactive session."""
    try: 
        get_ipython() # type: ignore
        return True
    except:
        return False

def pairwise(iterable: Iterable) -> Iterable:
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)

def read_a_leaf(stem: list[str], tree: MutableMapping[str, Any]) -> Optional[Any]:
    """Read the leaf at the end of the stem on the tree."""
    try:
        return reduce(lambda branch, leaf: branch[leaf], stem, tree)
    except KeyError:
        return None

def read_a_branch(stem: list[str], tree: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Read the branch at the end of the stem on the tree."""
    try:
        return dict(reduce(lambda branch, leaf: branch[leaf], stem, tree))
    except KeyError:
        return dict()
