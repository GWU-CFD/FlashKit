# type annotations
from __future__ import annotations
from typing import cast, NamedTuple, TYPE_CHECKING

# standard libraries
import logging
from functools import wraps, reduce

# internal libraries
from .configure import get_arguments, get_defaults
from .error import StreamError
from ..resources import CONFIG

# static analysis
if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from typing import Any, Callable, Dict, Optional, TypeVar
    F = TypeVar('F', bound=Callable[..., Any])
    D = Callable[[F], F]
    C = Callable[..., Dict[str, Any]]

# deal w/ runtime cast
else:
    F = None

logger = logging.getLogger(__name__)

# define public interface
__all__ = ['Instructions', 'build', 'extract', 'mail', 'pack', 'patch', 
           'prune', 'unpack', 'ship', 'strip', 'translate', ]

# define default constants
IGNORE = CONFIG['core']['stream']['ignore']
MSG_EXP = 'Unknown error while processing stream!'
MSG_KEY = 'Likely malformed or missing arguments in or crates on the stream!'

class Instructions(NamedTuple):
    """Helper class to assist in using decorator factories."""
    packages: Optional[Iterable[str]] = None
    route: Optional[Sequence[str]] = None
    priority: Optional[Iterable[str]] = None
    crates: Optional[Sequence[C]] = None
    drops: Optional[Iterable[str]] = None
    mapping: Mapping[str, str] = {}

def abstract(members: Sequence[str]) -> D:
    """Support abstracting decorator factories, with Instructions; 
    while retaining ability to directly call factories with args."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args):
            first, *_ = args
            if isinstance(first, Instructions):
                args = tuple(getattr(first, member) for member in members)
            return function(*args)
        return cast(F, wrapper)
    return decorator

def handler(function: F) -> F:
    """Support for error handeling for the stream."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except KeyError as error:
            raise StreamError(MSG_KEY) from error
    return cast(F, wrapper)

@abstract(('crates', ))
def build(crates: Sequence[F]) -> D:
    """Apply (build) the crates to (onto) the stream."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Building the stream.')
            for crate in crates:
                stream = crate(**stream)
            return function(**stream)
        return cast(F, wrapper)
    return decorator

@abstract(('packages', ))
def extract(packages: Iterable[str]) -> D:
    """Extract packages from the stream."""
    def decorator(function: F) -> F:
        def wrapper(**stream):
            logger.debug(f'Stream -- Extracting packages from stream.')
            return {key: value for key, value in stream.items() if key in packages}
        return cast(F, wrapper)
    return decorator

@abstract(('packages', 'route', 'priority', 'crates', 'drops', 'mapping', ))
def mail(packages: Iterable[str], route: Sequence[str], priority: Iterable[str],
         crates: Sequence[C], drops: Iterable[str], mapping: Mapping[str, str]) -> D:
    """Ship crated, pruned, and translated packages; applies ship-build-prune."""
    def decorator(function: F) -> F:
        @wraps(function)
        @handler
        def wrapper(**stream):
            logger.debug(f'Stream -- Mailing (i.e., ship, build, prune) the stream.')
            return ship(packages, route, priority)(build(crates)(prune(drops, mapping)(function)))(**stream)
        return cast(F, wrapper)
    return decorator

@abstract(('packages', 'route', 'priority', ))
def pack(packages: Iterable[str], route: Sequence[str], priority: Iterable[str]) -> D:
    """Ship packeges along route while, prioritizing (send through) some packages."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Packing the stream.')
            holds = {key: stream.get(key, None) for key in priority}
            holds = {key: item for key, item in holds.items() if item is not None}
            stream = {key: stream.get(key, None) for key in packages}
            stream = {key: item for key, item in stream.items() if item is not None}
            for leg in reversed(route):
                stream = {leg: stream}
            stream.update(**holds)
            return function(**stream)
        return cast(F, wrapper)
    return decorator

def patch(function: F) -> F:
    """Apply defaults and configs to the stream."""
    dispatch = {True: get_defaults, False: get_arguments}
    @wraps(function)
    def wrapper(**stream):
        logger.debug(f'Stream -- Patching the stream.')
        ignore = stream.get(IGNORE, False)
        stream = dispatch[ignore](local=stream)
        return function(**stream)
    return cast(F, wrapper)

@abstract(('drops', 'mapping', ))
def prune(drops: Iterable[str], mapping: Mapping[str, str]) -> D:
    """Prepare the stream; applies strip-translate"""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Pruning (i.e., strip, translate) the stream.')
            return strip(drops)(translate(mapping)(function))(**stream)
        return cast(F, wrapper)
    return decorator

@abstract(('route', 'priority', ))
def unpack(route: Sequence[str], priority: Iterable[str]) -> D:
    """Open shiped packages from route along with priority packages"""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Unpacking the stream.')
            holds = {key: stream.pop(key, None) for key in priority}
            holds = {key: item for key, item in holds.items() if item is not None}
            stream = reduce(lambda branch, leaf: branch[leaf], route, stream)
            stream.update(**holds)
            return function(**stream)
        return cast(F, wrapper)
    return decorator

@abstract(('packages', 'route', 'priority', ))
def ship(packages: Iterable[str], route: Sequence[str], priority: Iterable[str]) -> D:
    """Ship packages; applies pack-patch-unpack"""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Shipping (i.e., pack, patch, unpack) the stream.')
            return pack(packages, route, priority)(patch(unpack(route, priority)(function)))(**stream)
        return cast(F, wrapper)
    return decorator

@abstract(('drops', ))
def strip(drops: Iterable[str]) -> D:
    """Strip some (drops) packages from the stream."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Stripping the stream.')
            for drop in drops:
                stream.pop(drop, None)
            return function(**stream)
        return cast(F, wrapper)
    return decorator

@abstract(('mapping', ))
def translate(mapping: Mapping[str, str]) -> D:
    """Translate stream keys according to mapping."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream):
            logger.debug(f'Stream -- Translating the stream.')
            for key, value in mapping.items():
                store = stream.pop(key, None)
                if store is not None:
                    stream[value] = store
            return function(**stream)
        return cast(F, wrapper)
    return decorator
