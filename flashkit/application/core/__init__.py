"""Config file initialization for FlashKit."""

# standard libraries
from functools import partial 

# internal libraries
from ...resources import DEFAULTS, MAPPING
from .configure import gather, harvest, prepare

# initialize argument factory for commandline routines
get_arguments = partial(harvest, **prepare({'system': DEFAULTS}, MAPPING), trees=prepare(gather(), MAPPING))
get_defaults = partial(harvest, **prepare({'system': DEFAULTS}, MAPPING))
