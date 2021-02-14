"""Logging manager for the FlashKit library and python api."""

# standard libraries
import sys
import logging

# internal libraries
from ..resources import CONFIG

# define public interface
__all__ = ['console', 'debugger', 'logger', 'printer',  
           'CONSOLE', 'DEBUG', 'INFO', 'LOGGER', 'VERBOSE', 'WARN', ]

# default constants
CONSOLE = CONFIG['core']['logger']['console']
LOGGER = CONFIG['core']['logger']['logger']
PRINTER = CONFIG['core']['logger']['printer']
VERBOSE = CONFIG['core']['logger']['verbose']

# provide logging constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARN

# Configure a console handler
console = logging.StreamHandler(sys.stdout)
console.setLevel(INFO)
console.setFormatter(logging.Formatter(CONSOLE))

# Initialize flashkit printer (console logging)
printer = logging.getLogger(PRINTER)
printer.setLevel(INFO)
printer.addHandler(console)

# Configure a stderr handler
debugger = logging.StreamHandler(sys.stderr)
debugger.setLevel(WARN)
debugger.setFormatter(logging.Formatter(VERBOSE))

# Initialize flashkit logger
logger = logging.getLogger(LOGGER)
logger.setLevel(WARN)
logger.addHandler(debugger)

