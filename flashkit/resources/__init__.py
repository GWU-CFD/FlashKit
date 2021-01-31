"""Resources initialization for FlashKit."""

# standard libraries
import importlib.resources as pkg_resources

# internal libraries
from .. import resources

# external libraries
import toml

with pkg_resources.path(resources, 'defaults.toml') as file:
    DEFAULTS = toml.load(file)
