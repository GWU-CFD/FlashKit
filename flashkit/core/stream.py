# type annotations
from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING

# standard libraries
from functools import wraps, reduce

# internal libraries
from ..resources import CONFIG
from .configure import get_arguments, get_defaults

# static analysis
if TYPE_CHECKING:
    from typing import Any, Callable, TypeVar
    from collections.abc import Iterable, Mapping, Sequence
    F = TypeVar('F', bound = Callable[..., Any])
    D = TypeVar('D', bound = Callable[[F], F])
    S = TypeVar('S', bound = dict[str, Any])

# define public interface
__all__ = ['Instructions', 'build', 'extract', 'mail', 'pack', 'patch', 
           'prune', 'unpack', 'ship', 'strip', 'translate', ]

# default constants
IGNORE = CONFIG['core']['stream']['ignore']

class Instructions(NamedTuple):
    """Helper class to assist in using decorator factories."""
    packages: Optional[Iterable[str]] = None
    route: Optional[Sequence[str]] = None
    priority: Optional[Iterable[str]] = None
    crates: Optional[Sequence[Callable[[S], S]]] = None
    drops: Optional[Iterable[str]] = None
    mapping: Optional[Mapping[str, str]] = None

def abstract(members: Sequence[str]) -> D:
    """Support abstracting decorator factories, with Instructions; 
    while retaining ability to directly call factories with args."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args: Any) -> F:
            first, *_ = args
            if isinstance(first, Instructions):
                args = tuple(getattr(first, member) for member in members)
            return function(*args)
        return wrapper
    return decorator

@abstract(('crates', ))
def build(crates: Sequence[Callable[[S], S]]) -> D:
    """Apply (build) the crates to (onto) the stream."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            for crate in crates:
                stream = crate(**stream)
            return function(**stream)
        return wrapper
    return decorator

@abstract(('packages', ))
def extract(packages: Iterable[str]) -> D:
    """Extract packages from the stream."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            return {key: value for key, value in stream.items() if key in packages}
        return wrapper
    return decorator

@abstract(('packages', 'route', 'priority', 'crates', 'drops', 'mapping', ))
def mail(packages: Iterable[str], route: Sequence[str], priority: Iterable[str],
         crates: Sequence[Callable[[S], S]], drops: Iterable[str], mapping: Mapping[str, str]) -> D:
    """Ship crated, pruned, and translated packages; applies ship-build-prune."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            return ship(packages, route, priority)(build(crates)(prune(drops, mapping)(function)))(**stream)
        return wrapper
    return decorator

@abstract(('packages', 'route', 'priority', ))
def pack(packages: Iterable[str], route: Sequence[str], priority: Iterable[str]) -> D:
    """Ship packeges along route while, prioritizing (send through) some packages."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            holds = {key: stream.get(key, None) for key in priority}
            holds = {key: item for key, item in holds.items() if item is not None}
            stream = {key: stream.get(key, None) for key in packages}
            stream = {key: item for key, item in stream.items() if item is not None}
            for leg in reversed(route):
                stream = {leg: stream}
            stream.update(**holds)
            return function(**stream)
        return wrapper
    return decorator

def patch(function: F) -> F:
    """Apply defaults and configs to the stream."""
    dispatch = {True: get_defaults, False: get_arguments}
    @wraps(function)
    def wrapper(**stream: S) -> S:
        ignore = stream.get(IGNORE, False)
        stream = dispatch[ignore](local=stream)
        return function(**stream)
    return wrapper

@abstract(('drops', 'mapping', ))
def prune(drops: Iterable[str], mapping: Mapping[str, str]) -> D:
    """Prepare the stream; applies strip-translate"""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            return strip(drops)(translate(mapping)(function))(**stream)
        return wrapper
    return decorator

@abstract(('route', 'priority', ))
def unpack(route: Sequence[str], priority: Iterable[str]) -> D:
    """Open shiped packages from route along with priority packages"""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            holds = {key: stream.pop(key, None) for key in priority}
            holds = {key: item for key, item in holds.items() if item is not None}
            stream = reduce(lambda branch, leaf: branch[leaf], route, stream)
            stream.update(**holds)
            return function(**stream)
        return wrapper
    return decorator

@abstract(('packages', 'route', 'priority', ))
def ship(packages: Iterable[str], route: Sequence[str], priority: Iterable[str]) -> D:
    """Ship packages; applies pack-patch-unpack"""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            return pack(packages, route, priority)(patch(unpack(route, priority)(function)))(**stream)
        return wrapper
    return decorator

@abstract(('drops', ))
def strip(drops: Iterable[str]) -> D:
    """Strip some (drops) packages from the stream."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            for drop in drops:
                stream.pop(drop, None)
            return function(**stream)
        return wrapper
    return decorator

@abstract(('mapping', ))
def translate(mapping: Mapping[str, str]) -> D:
    """Translate stream keys according to mapping."""
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(**stream: S) -> S:
            for key, value in mapping.items():
                store = stream.pop(key, None)
                if store is not None:
                    stream[value] = store
            return function(**stream)
        return wrapper
    return decorator