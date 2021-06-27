"""Support for custom types, boilerplate, and monkey patching for Application and Interface classes."""

# type annotations
from __future__ import annotations
from typing import TYPE_CHECKING

# internal libraries
from ..core.logging import logger 
from ..core.parallel import is_root, squash

# external libraries
from cmdkit import app
from cmdkit.app import Application, exit_status
from cmdkit.cli import ArgumentError

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, Type
    DictApp = Dict[str, Type[Application]]

# deal w/ runtime import
else:
    DictApp = None

# define library (public) interface
__all__ = ['patched_error', 'patched_exceptions', ]

# inject logger back into cmdkit library
Application.log_critical = logger.critical
Application.log_exception = logger.exception

# inject root limited version and help options
setattr(Application, 'handle_help', squash(Application.handle_help))
setattr(Application, 'handle_version', squash(Application.handle_version))
setattr(Application, 'handle_usage', squash(Application.handle_usage))

# inject redefinition of usage message as a success
setattr(app, 'exit_status', exit_status._replace(usage = 0))

# Create custom error handeling interfaces (monkey patch Application)
def patched_error(patch: str) -> Callable[..., None]:
    """Factory to override simple raise w/ formatted message."""
    def wrapper(message: str) -> None:
        raise ArgumentError('\n'.join((patch, message)))
    logger.debug(f'core -- Providing an ArgumentError w/ message wrapper.')
    return wrapper

def patched_exceptions(patch: str, errors: Iterable[Type[Exception]] = [Exception, ]) -> dict[Type[Exception], Callable[[Exception], int]]:
    """Create dictionary based dispatcher for exception handeling."""
    logger.debug(f'core -- Providing an dictionary of logger patched handlers.')
    return {error: patched_logging(patch) for error in errors}

def patched_logging(patch: str) -> Callable[[Exception], int]:
    """Factory for patching custom exeption handlers."""
    def wrapper(exception: Exception, status: int = exit_status.runtime_error) -> int:
        message, *_ = exception.args
        message = f'{type(exception).__name__}( {message} )'
        if is_root(): Application.log_critical('\n'.join((patch, message)))
        return status
    return wrapper
