"""Logging manager for the FlashKit library and python api."""

# type annotations
from __future__ import annotations
from typing import Union

# standard libraries
import logging
import logging.handlers
import os
import sys

# internal libraries
from .parallel import is_root
from ..resources import CONFIG

# define library (public) interface
__all__ = ['force_debug', ]

# default constants
CONSOLE = CONFIG['core']['logger']['console']
ERROR = CONFIG['core']['logger']['error']
RECORD = CONFIG['core']['logger']['record']
TRACE = CONFIG['core']['logger']['trace']
LOGFILE = CONFIG['core']['logger']['logfile']
EXCFILE = CONFIG['core']['logger']['excfile']

HOME = os.path.expanduser('~/.flashkit')

# Configure a console handler
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.addFilter(lambda record: record.levelno <= logging.INFO)
console.setFormatter(logging.Formatter(CONSOLE))

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
    """Force the use of debugging logging level"""
    if state: logger.setLevel(logging.DEBUG)
    logger.debug('Force -- DEBUG Logging Level!')

def force_debug_console(state: bool = True) -> None:
    """Force the use of debugging logging level on console"""
    if state: console.setLevel(logging.DEBUG)
    logger.debug('Force -- DEBUG Logging Level @ Console!')
