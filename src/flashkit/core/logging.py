"""Logging manager for the FlashKit library and python api."""

# type annotations
from __future__ import annotations
from typing import Union

# standard libraries
import sys
import logging

# internal libraries
from ..resources import CONFIG

# define public interface
__all__ = ['CONSOLE', 'DEBUG', 'INFO', 'LOGGER', 'VERBOSE', 'WARN',
           'console', 'debugger', 'logger', 'printer', ]

# default constants
CONSOLE = CONFIG['core']['logger']['console']
DEBUGGER = CONFIG['core']['logger']['debugger']
LOGGER = CONFIG['core']['logger']['logger']
PRINTER = CONFIG['core']['logger']['printer']
SIMPLE = CONFIG['core']['logger']['simple']

# provide logging constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARN

class Simple:
    """Interface consistant but uses print.""" 
    def __init__(self):
        self.level = INFO

    def setLevel(self, level: int) -> None:
        self.level = level

    def debug(self, message: str) -> None:
        self.write(message)

    def info(self, message: str) -> None:
        self.write(message)
    
    def warn(self, message: str) -> None:
        self.write(message)

    def write(self, message: str) -> None:
        print(message)

# Configure a console handler
console = logging.StreamHandler(sys.stdout)
console.setLevel(INFO)
console.setFormatter(logging.Formatter(CONSOLE))

# Configure a stderr handler
debugger = logging.StreamHandler(sys.stderr)
debugger.setLevel(DEBUG)
debugger.setFormatter(logging.Formatter(DEBUGGER))

# Initialize flashkit printer (console logging)
printer: Union[Simple, logging.Logger]
if SIMPLE:
    printer = Simple()
else:
    printer = logging.getLogger(PRINTER)
    printer.addHandler(console)
printer.setLevel(INFO)  

# Initialize flashkit logger
logger = logging.getLogger(LOGGER)
logger.setLevel(WARN)
logger.addHandler(debugger)
