"""Support for custom actions, boilerplate, and type parsing for Application classes and elsewhere."""

# type annotations
from __future__ import annotations
from typing import Any, Callable, Dict, Iterable, Union, Type

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

# Create commands custom type
DictApp = Dict[str, Type[Application]]

# define library (public) interface
__all__ = ['patched_error', 'patched_exceptions', 'ListInt', 'ListFloat', 'DictStr']

# inject logger back into cmdkit library
Application.log_critical = logger.critical
Application.log_exception = logger.exception

# Create safe and sensical type coersion (conversion)
def none(arg: Any) -> None:
    """Coerce if should convert to NoneType."""
    if str(arg).lower() not in (str(None).lower(), 'null'):
        raise ValueError()
    return None

def logical(arg: Any) -> bool:
    """Coerce if should convert to bool."""
    if str(arg).lower() not in (str(b).lower() for b in {True, False}):
        raise ValueError()
    return bool(arg)

def SafeInt(value: Any) -> Union[int, str]:
    """Provide pythonic conversion to int that fails to str."""
    try:
        return int(value)
    except ValueError:
        return str(value)

def SafeFloat(value: Any) -> Union[float, str]:
    """Provide pythonic conversion to float that fails to str."""
    try:
        return float(value)
    except ValueError:
        return str(value)

def SafeAny(arg: Any) -> Union[bool, int, float, None, str]:
    """Provide pythonic conversion to sensical type that fails to str."""
    arg = str(arg)
    for func in (logical, int, float, none):
        try:
            return func(arg) # type: ignore
        except ValueError:
            next
    return arg

# Create argpase List custom types
def ListInt(s: str) -> list[int]:
    """Parse a string of format <VALUE, ...> into a list of ints.""" 
    return [int(i) for i in re.split(r',\s|,|\s', s)]

def ListFloat(s: str) -> list[float]:
    """Parse a string of format <VALUE, ...> into a list of floats.""" 
    return [float(i) for i in re.split(r',\s|,|\s', s)]

def DictStr(s: str) -> dict[str, str]:
    """Parse a string of format <KEY=VALUE, ...> into a dictionary of strings."""
    return dict((k.strip(), v.strip()) for k, v in (re.split(r'=\s|=', i) for i in re.split(r',\s|,', s)))

def DictAny(s: str) -> dict[str, Union[bool, int, float, None, str]]:
    """Parse a string of format <KEY=VALUE, ...> into a dictionary of actual types."""
    return dict((k.strip(), SafeAny(v.strip())) for k, v in (re.split(r'=\s|=', i) for i in re.split(r',\s|,', s)))

def DictDictStr(s: str) -> dict[str, dict[str, str]]:
    """Parse a string of format <OPT={KEY=VALUE, ...}, ...> into a nested dictionary of strings."""
    return dict((k.strip(), DictStr(v.strip())) for k, v in [re.split(r'={|=\s{', i) for i in re.split(r'},|}\s,', s[:-1])])

def DictDictAny(s: str) -> dict[str, dict[str, Union[bool, int, float, None, str]]]:
    """Parse a string of format <OPT={KEY=VALUE, ...}, ...> into a nested dictionary of strings."""
    return dict((k.strip(), DictAny(v.strip())) for k, v in [re.split(r'={|=\s{', i) for i in re.split(r'},|}\s,', s[:-1])])

# Create custom argparse actions
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

# Create custom error handeling interfaces (monkey patch Application)
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