"""Provides useful errors raised by FlashKit."""

class AutoError(Exception):
    """Raised when cannot automatically determine a behavior."""

class LibraryError(Exception):
    """Raised when handling errors raised by library or support modules."""

class ParallelError(Exception):
    """Available for handling errors raised by parallel module"""

class StreamError(Exception):
    """Raised when plausable errors are thrown processing the stream."""
