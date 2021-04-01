"""Simple tools that support library functions and elsewhere."""

# type annotations
from __future__ import annotations

# define library (public) interface
__all__ = ['first_true', ]

def first_true(iterable, predictor):
    return next(filter(predictor, iterable))

