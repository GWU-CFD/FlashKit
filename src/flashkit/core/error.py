"""Provides useful errors raised by FlashKit."""

# type annotations
from __future__ import annotations
from typing import Any, Callable

# standard libraries
import sys
from functools import wraps

# internal libraries
from .logging import handle_exception

# define library (public) interface
__all__ = ['AutoError', 'LibraryError', 'ParallelError', 'StreamError',
           'error', ]

class AutoError(Exception):
    """Raised when cannot automatically determine a behavior."""

class LibraryError(Exception):
    """Raised when handling errors raised by library or support modules."""

class ParallelError(Exception):
    """Available for handling errors raised by parallel module"""

class StreamError(Exception):
    """Raised when plausable errors are thrown processing the stream."""

def error(patch: str = '') -> Any:
    """Factory for api functions with exeption handlers."""
    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapper(**kwargs):
            try:
                return function(**kwargs)
            except Exception as error:
                handle_exception(error, patch)
                sys.exit()
        return wrapper
    return decorator
