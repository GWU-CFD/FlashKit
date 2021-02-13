"""Provides useful errors raised by FlashKit."""

class AutoError(Exception):
    """Raised when cannot automatically determine a behavior."""

class StreamError(Exception):
    """Raised when plausable errors are thrown processing the stream."""
