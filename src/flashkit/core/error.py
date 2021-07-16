"""Provides useful errors raised by FlashKit."""

# type annotations
from __future__ import annotations
from typing import Any, Callable

# standard libraries
import logging
import sys
import traceback
from functools import wraps

# internal libraries
from .tools import is_ipython

logger = logging.getLogger('flashkit')

# define library (public) interface
__all__ = ['AutoError', 'LibraryError', 'ParallelError', 'StreamError',
           'handle_exception', 'error', ]

class AutoError(Exception):
    """Raised when cannot automatically determine a behavior."""

class LibraryError(Exception):
    """Raised when handling errors raised by library or support modules."""

class ParallelError(Exception):
    """Available for handling errors raised by parallel module"""

class StreamError(Exception):
    """Raised when plausable errors are thrown processing the stream."""

def handle_exception(exception: Exception, patch: str = '') -> None:
    """Handle the traceback output."""
    tb = ''.join(traceback.format_exc())
    message, *_ = exception.args
    logger.error('\n'.join((patch, f'{type(exception).__name__}( {message} )')))
    logger.log(logging.CRITICAL + 1, f'An unhandled exception occured: {message}\n\n{tb}')

def error(patch: str = '') -> Any:
    """Factory for api functions with exeption handlers."""
    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapper(**kwargs):
            try:
                return function(**kwargs)
            except Exception as error:
                handle_exception(error, patch)
                if not is_ipython(): sys.exit()
        return wrapper
    return decorator
