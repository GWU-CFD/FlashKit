"""Define argparse custom actions and some option implementations."""

# type annotations
from __future__ import annotations

# standard libraries
import argparse

# internal libraries
from ..core.configure import force_delayed, get_defaults
from ..core.logging import logger, printer, DEBUG
from ..core.parallel import force_parallel, is_root
from ..resources import MAPPING, TEMPLATES

# external libraries
from cmdkit.config import Namespace

# define library (public) interface
__all__ = ['force_debug', 'return_available', 'return_options',
           'DebugLogging', 'ForceDelayed', 'ForceParallel']

def force_debug(state: bool = True) -> None:
    """Force the use of debugging logging level;
    needs to be here vice logging to prevent a circular import."""
    if state: logger.setLevel(DEBUG)
    if is_root(): logger.debug('Force -- DEBUG Logging Level!')

class DebugLogging(argparse.Action):
    """Create custom action for setting debug logging."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        force_debug()

class ForceDelayed(argparse.Action):
    """Create custom action for setting delayed configuration enviornment."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        force_delayed()

class ForceParallel(argparse.Action):
    """Create custom action for setting parallel enviornment."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        force_parallel()

def return_available(category: str, tags: list[str]) -> None:
    """Force the logging of available template options for flashkit."""
    printer.info(
            f'The following library template key/value pairs are provided:\n'
            f'with the tags of <{tags}> defined in each section')
    for section, layout in TEMPLATES[category].items():
        printer.info(f'\n Section: {section}\n')
        for tag, values in layout.items():
            if tag in tags:
                printer.info(
                    f'Parameter\t{tag}\n'
                    f'---------\t{"-"*len(tag)}')
                printer.info('\n'.join(f'{tmp}\t\t{value}' for tmp, value in values.items()))

def return_options(category: str, operation: str) -> None:
    """Force the logging of defaults and mappings for flashkit <category> <operation>."""
    flatten = lambda value: (value if value != '' else '--') if not isinstance(value, Namespace) else dict(value)
    defaults = '\n'.join(f'{opt}\t\t{flatten(value)}'
            for opt, value in get_defaults()[category][operation].items())
    mappings = '\n\n'.join(f"{opt}\t\t[{'.'.join(path)}]\n\t\t{gen} = ..."
            for opt, (*path, gen) in MAPPING[category][operation].items())
    message = (
        f'The following library defaults are provided for flashkit {category} {operation}:\n'
        f'\n'
        f'Options\t\tDefault Values\n'
        f'-------\t\t--------------\n'
        f'{defaults}\n'
        f'\n\n'
        f'The following outlines the general section options, which can be mapped\n'
        f'in the configuration file, that are provided for flashkit {category} {operation}:\n'
        f'\n'
        f'Options\t\tflash.toml Sections and Options\n'
        f'-------\t\t-------------------------------\n'
        f'{mappings}\n'
        )
    printer.info(message)

