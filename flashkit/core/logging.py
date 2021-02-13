
# standard libraries
from contextlib import contextmanager
import logging

# Configure a handler for logging
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(msg)s'))

# Initialize flashkit logger
logger = logging.getLogger('flashkit')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
