"""Logging manager for the FlashKit library and python api."""

# type annotations
from __future__ import annotations
from cmath import log
from typing import Union

# standard libraries
import logging
import logging.handlers
import os
import sys

from flashkit.core.progress import TERMINAL

# internal libraries
from .parallel import is_root
from ..resources import CONFIG

# define library (public) interface
__all__ = ['force_debug', ]

# default constants
CONSOLE = CONFIG['core']['logger']['console']
ERROR = CONFIG['core']['logger']['error']
EXCFILE = CONFIG['core']['logger']['excfile']
FILTER = CONFIG['core']['logger']['filter']
LOGFILE = CONFIG['core']['logger']['logfile']
RECORD = CONFIG['core']['logger']['record']
TRACE = CONFIG['core']['logger']['trace']
BLANKING = CONFIG['core']['progress']['blanking']
TERMINAL = CONFIG['core']['progress']['terminal']

HOME = os.path.expanduser('~/.flashkit')

class ConsoleFormatter(logging.Formatter):
    def format(self, record):
        self._style._fmt = CONSOLE
        return super().format(record).ljust(TERMINAL, BLANKING)

class LibraryFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.INFO:
            return True
        elif record.levelno >= logging.DEBUG:
            return any(f in record.pathname for f in FILTER)
        else:
            return False

# Configure a console handler
filter = LibraryFilter()
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.addFilter(lambda record: record.levelno <= logging.INFO)
console.setFormatter(ConsoleFormatter())

# Configure a stderr handler
error = logging.StreamHandler(sys.stderr)
error.setLevel(logging.WARNING)
error.addFilter(lambda record: logging.CRITICAL >= record.levelno >= logging.WARNING)
error.setFormatter(logging.Formatter(ERROR))

# Configure a record handler
record = logging.handlers.RotatingFileHandler(os.path.join(HOME, LOGFILE), maxBytes=5*1024*1024, backupCount=2, delay=True)
record.setLevel(logging.DEBUG)
record.addFilter(lambda record: record.levelno <= logging.CRITICAL)
record.setFormatter(logging.Formatter(RECORD, '%Y-%m-%d %H:%M:%S'))

# Configure a traceback handler
tracer = logging.handlers.RotatingFileHandler(os.path.join(HOME, EXCFILE), maxBytes=5*1024*1024, backupCount=2, delay=True)
tracer.setLevel(logging.CRITICAL)
tracer.addFilter(lambda record: record.levelno >= logging.CRITICAL)
tracer.setFormatter(logging.Formatter(TRACE, '%Y-%m-%d %H:%M:%S'))

# Configure a handler for non-root processes
default = logging.NullHandler()

# Initialize flashkit logger
logger = logging.getLogger('flashkit')
logger.addHandler(default)
logger.setLevel(logging.INFO)

if is_root():
    if not os.path.exists(HOME):
        os.makedirs(HOME)
    
    logger.addHandler(record)
    logger.addHandler(tracer)
    logger.info('########## Flashkit Called ##########')
    logger.addHandler(console)
    logger.addHandler(error)

def force_debug(state: bool = True) -> None:
    """Force the use of all debugging logging"""
    if state: 
        console.removeFilter(filter)
        record.removeFilter(filter)
        logger.debug('Force -- Debug Logging Level!')
    else:
        console.addFilter(filter)
        record.addFilter(filter)
        logger.debug('Attempted to unset debug logging level.')

def force_verbose(state: bool = True) -> None:
    """Force the use of debugging logging level"""
    if state: 
        logger.setLevel(logging.DEBUG)
        console.setLevel(logging.DEBUG)
        console.addFilter(filter)
        record.addFilter(filter)
        logger.debug('Force -- Verbose Logging Level!')
    else:
        logger.debug('Attempted to unset debug logging level.')
        logger.setLevel(logging.INFO)
        console.setLevel(logging.INFO)
        console.removeFilter(filter)
        record.removeFilter(filter)