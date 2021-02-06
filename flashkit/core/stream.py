# type annotations
from __future__ import annotations

# standard libraries
from functools import wraps, reduce

# internal libraries
from ..resources import CONFIG
from .configure import get_arguments, get_defaults

# default constants
IGNORE = CONFIG['core']['stream']['ignore']

def extract(labels):
    """Extract labels from the stream."""
    def extracter(function):
        @wraps(function)
        def extracted(**stream):
            return {key: value for key, value in stream.items() if key in labels}
        return extracted
    return extracter

def pack(labels, route, priority):
    """Ship labeled packeges along route while, prioritizing some packages."""
    def packer(function):
        @wraps(function)
        def packed(**stream):
            holds = {key: stream.get(key, None) for key in priority}
            holds = {key: item for key, item in holds.items() if item is not None}
            stream = {key: stream.get(key, None) for key in labels}
            stream = {key: item for key, item in stream.items() if item is not None}
            for leg in reversed(route):
                stream = {leg: stream}
            stream.update(**holds)
            return function(**stream)
        return packed
    return packer

def patch(function):
    """Apply defaults and configs to the stream."""
    @wraps(function)
    def patched(**stream):
        ignore = stream.get(IGNORE, False)
        if ignore:
            stream = get_defaults(local=stream)
        else:
            stream = get_arguments(local=stream)
        return function(**stream)
    return patched

def unpack(labels, route, priority):
    """Open shiped packages from route along with priority packages"""
    def unpacker(function):
        @wraps(function)
        def unpacked(**stream):
            holds = {key: stream.pop(key, None) for key in priority}
            holds = {key: item for key, item in holds.items() if item is not None}
            stream = reduce(lambda branch, leaf: branch[leaf], route, stream)
            stream.update(**holds)
            return function(**stream)
        return unpacked
    return unpacker

def ship(packages, route, priority):
    """Ship packages; applies pack-patch-unpack"""
    def shipper(function):
        @wraps(function)
        def shipped(**stream):
            return pack(packages, route, priority)(patch(unpack(packages, route, priority)(function)))(**stream)
        return shipped
    return shipper

def ship_clean(packages, route, priority):
    """Ship clean packages; applies pack-patch-unpack-strip"""
    def arrive(function):
        @wraps(function)
        def arrived(**stream):
            return ship(packages, route, priority)(strip(priority)(function))(**stream)
        return arrived 
    return arrive

def strap(buckle):
    """Apply the buckle to the stream."""
    def strapper(function):
        @wraps(function)
        def strapped(**stream):
            return function(**buckle(**stream))
        return strapped
    return strapper

def strip(labels):
    """Strip labels from the stream."""
    def stripper(function):
        @wraps(function)
        def stripped(**stream):
            for label in labels:
                stream.pop(label, None)
            return function(**stream)
        return stripped
    return stripper

def translate(mapping):
    """Translate stream keys according to mapping."""
    def translater(function):
        @wraps(function)
        def translated(**stream):
            for key, value in mapping.items():
                store = stream.pop(key, None)
                if store is not None:
                    stream[value] = store
            return function(**stream)
        return translated
    return translater
