"""Core (sub-library) initialization for FlashKit."""

# internal libraries
from .parallel import is_root
from .logging import attach_api_handlers 

if is_root():
    attach_api_handlers()
