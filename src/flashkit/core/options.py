"""Define argparse custom actions and some option implementations."""

# type annotations
from __future__ import annotations

# standard libraries
import argparse

# internal libraries
from ..core.configure import force_delayed, get_defaults
from ..core.logging import force_debug
from ..core.parallel import force_parallel
from ..resources import CONFIG, MAPPING, TEMPLATES

# external libraries
from cmdkit.config import Namespace

# define library (public) interface
__all__ = ['return_available', 'return_options',
           'DebugLogging', 'ForceDelayed', 'ForceParallel']

# define configuration constants (internal)
MIN_DEF = CONFIG['core']['options']['mindef']
MIN_MAP = CONFIG['core']['options']['minmap']
PAD_DEF = CONFIG['core']['options']['paddef']
PAD_MAP = CONFIG['core']['options']['padmap']

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

def return_available(category: str, tags: list[str], skips: list[str] = []) -> None:
    """Force the logging of available template options for flashkit."""
    print(
            f'The following library template key/value pairs are provided:\n'
            f'with the tags of <{tags}> defined in each section')
    for section, layout in TEMPLATES[category].items():
        if section in skips: continue
        print(f'\n Section: {section}\n')
        for tag, values in layout.items():
            if tag in tags:
                print(
                    f'Parameter\t{tag}\n'
                    f'---------\t{"-"*len(tag)}')
                print('\n'.join(f'{tmp}\t\t{value}' for tmp, value in values.items()))

def return_options(category: str, operation: str) -> None:
    """Force the logging of defaults and mappings for flashkit <category> <operation>."""
    flatten = lambda value: (value if value != '' else '--') if not isinstance(value, Namespace) else dict(value)
    coldef = max([len(opt) for opt in get_defaults()[category][operation]] + [MIN_DEF, ]) + PAD_DEF
    colmap = max([len(opt) for opt in MAPPING[category][operation]] + [MIN_MAP, ]) + PAD_MAP
    defaults = '\n'.join(f'{opt: <{coldef}} {flatten(value)}'
            for opt, value in get_defaults()[category][operation].items())
    mappings = '\n\n'.join(f"{opt: <{colmap}} [{'.'.join(path)}]\n{' '*colmap} {gen} = ..."
            for opt, (*path, gen) in MAPPING[category][operation].items())
    message = (
        f'The following library defaults are provided for flashkit {category} {operation}:\n'
        f'\n'
        f'{"Options": <{coldef}} Default Values\n'
        f'{"-------": <{coldef}} --------------\n'
        f'{defaults}\n'
        f'\n\n'
        f'The following outlines the general section options, which can be mapped\n'
        f'in the configuration file, that are provided for flashkit {category} {operation}:\n'
        f'\n'
        f'{"Options": <{colmap}} flash.toml Sections and Options\n'
        f'{"-------": <{colmap}} -------------------------------\n'
        f'{mappings}\n'
        )
    print(message)
