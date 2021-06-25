"""Simple tools that support library functions and elsewhere."""

# type annotations
from __future__ import annotations
from typing import Any, Optional
from collections.abc import MutableMapping

# standard libraries
from functools import reduce

# define library (public) interface
__all__ = ['first_true', 'read_a_leaf']

def first_true(iterable, predictor):
    return next(filter(predictor, iterable))

def read_a_leaf(stem: list[str], tree: MutableMapping[str, Any]) -> Optional[Any]:
    """Read the leaf at the end of the stem on the treee."""
    try:
        return reduce(lambda branch, leaf: branch[leaf], stem, tree)
    except KeyError:
        return None
