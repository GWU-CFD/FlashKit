"""Resources initialization for FlashKit."""

# standard libraries
import importlib.resources as pkg_resources

# external libraries
import toml

__all__ = ['DEFAULTS', 'CONFIG', 'MAPPING', 'TEMPLATES']

with pkg_resources.path(__package__, 'defaults.toml') as file:
    DEFAULTS = toml.load(file)

with pkg_resources.path(__package__, 'config.toml') as file:
    CONFIG = toml.load(file)

with pkg_resources.path(__package__, 'mapping.toml') as file:
    MAPPING = toml.load(file)

with pkg_resources.path(__package__, 'templates.toml') as file:
    TEMPLATES = toml.load(file)
