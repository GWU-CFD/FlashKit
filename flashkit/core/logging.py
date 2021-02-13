"""Logging manager for the FlashKit library and python api."""

# standard libraries
from contextlib import contextmanager
import logging

# internal libraries
from ..resources import CONFIG

# define public interface
__all__ = ['logger', ]

# default constants
FORM = CONFIG['core']['logger']['format']
NAME = CONFIG['core']['logger']['logger']

# Configure a handler for logging
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(FORM))

# Initialize flashkit logger
logger = logging.getLogger(NAME)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
