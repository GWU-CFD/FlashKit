"""Package initialization for FlashKit."""

# standard libraries
import logging

# ensure called before children
logger = logging.getLogger('flashkit')

# expose python interface
from . import api as flash
