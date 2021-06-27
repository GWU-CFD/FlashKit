"""Logging manager for the FlashKit library and python api."""

# type annotations
from __future__ import annotations
from typing import Union

# standard libraries
import logging
import sys
import traceback

# internal libraries
from ..resources import CONFIG

# define library (public) interface
__all__ = ['logger', 'attach_api_handlers', 'attach_cli_handlers', 
           'force_debug', 'handle_exception', ]

# default constants
CONSOLE = CONFIG['core']['logger']['console']
ERROR = CONFIG['core']['logger']['error']
RECORD = CONFIG['core']['logger']['record']
TRACE = CONFIG['core']['logger']['trace']
LOGFILE = CONFIG['core']['logger']['logfile']
EXCFILE = CONFIG['core']['logger']['excfile']
LOGGER = CONFIG['core']['logger']['logger']

# Configure a console handler
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.addFilter(lambda record: record.levelno <= logging.INFO)
console.setFormatter(logging.Formatter(CONSOLE))

# Configure a stderr handler
error = logging.StreamHandler(sys.stderr)
error.setLevel(logging.WARNING)
error.addFilter(lambda record: logging.CRITICAL > record.levelno >= logging.WARNING)
error.setFormatter(logging.Formatter(ERROR))

# Configure a record handler
record = logging.FileHandler(LOGFILE)
record.setLevel(logging.DEBUG)
record.addFilter(lambda record: record.levelno < logging.CRITICAL)
record.setFormatter(logging.Formatter(RECORD, '%Y-%m-%d %H:%M:%S'))

# Configure a traceback handler
tracer = logging.FileHandler(EXCFILE)
tracer.setLevel(logging.CRITICAL)
tracer.addFilter(lambda record: record.levelno >= logging.CRITICAL)
tracer.setFormatter(logging.Formatter(TRACE, '%Y-%m-%d %H:%M:%S'))

# Configure a handler for non-root processes
default = logging.NullHandler()

# Initialize flashkit logger
logger = logging.getLogger(LOGGER)
logger.addHandler(default)
logger.setLevel(logging.INFO)

def attach_api_handlers() -> None:
    """Initialize logging, only for root"""
    logger.addHandler(error)
    logger.addHandler(record)
    logger.addHandler(tracer)

def attach_cli_handlers() -> None:
    """Initialize logging, only for root"""
    logger.addHandler(console)

def force_debug(state: bool = True) -> None:
    """Force the use of debugging logging level"""
    if state: logger.setLevel(logging.DEBUG)
    logger.debug('Force -- DEBUG Logging Level!')

def handle_exception(exception: Exception, patch: str = '') -> None:
    """Handle the traceback output."""
    tb = ''.join(traceback.format_exc())
    message, *_ = exception.args
    logger.error('\n'.join((patch, f'{type(exception).__name__}( {message} )')))
    logger.critical(f'An unhandled exception occured: {message}\n\n{tb}')
