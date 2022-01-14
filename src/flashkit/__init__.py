"""Package initialization for FlashKit."""

# standup the logging interface
from .core import logging

# expose python interface
from . import api as flash
