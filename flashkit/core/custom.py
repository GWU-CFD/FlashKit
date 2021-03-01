"""Support for custom actions, boilerplate, and type parsing for Application classes."""

# type annotations
from __future__ import annotations
from typing import Callable, Dict, Iterable, Type

# standard libraries
import argparse
import os
import re
import sys

# internal libraries
from ..core.logging import logger, DEBUG
from ..core.parallel import force_parallel, is_root, squash

# external libraries
from cmdkit.app import Application, exit_status
from cmdkit.cli import Interface, ArgumentError 

# define library (public) interface
__all__ = ['patched_error', 'patched_exceptions', 'ListInt', 'ListFloat', 'DictStr']

# inject logger back into cmdkit library
Application.log_critical = logger.critical
Application.log_exception = logger.exception

# Create argpase List custom types
ListInt = lambda l: [int(i) for i in re.split(r',\s|,|\s', l)] 
ListFloat = lambda l: [float(i) for i in re.split(r',\s|,|\s', l)] 
DictStr = lambda d: dict((k.strip(), v.strip()) for k, v in (re.split(r'=\s|=', i) for i in re.split(r',\s|,', d)))

# Create commands custom type
DictApp = Dict[str, Type[Application]]

class DebugLogging(argparse.Action):
    """Create custom action for setting debug logging."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        logger.setLevel(DEBUG)
        if is_root(): logger.debug('Set Logging Level To DEBUG!')

class ForceParallel(argparse.Action):
    """Create custom action for setting parallel enviornment."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        force_parallel()

def patched_error(patch: str) -> Callable[..., None]:
    """Factory to override simple raise w/ formatted message."""
    def wrapper(message: str) -> None:
        raise ArgumentError('\n'.join((patch, message)))
    return wrapper

def patched_exceptions(patch: str, errors: Iterable[Type[Exception]] = [Exception, ]) -> dict[Type[Exception], Callable[[Exception], int]]:
    """Create dictionary based dispatcher for exception handeling."""
    return {error: patched_logging(patch) for error in errors}

def patched_logging(patch: str) -> Callable[[Exception], int]:
    """Factory for patching custom exeption handlers."""
    def wrapper(exception: Exception, status: int = exit_status.runtime_error) -> int:
        message, *_ = exception.args
        message = f'{type(exception).__name__}( {message} )'
        if is_root(): Application.log_critical('\n'.join((patch, message)))
        return status
    return wrapper
