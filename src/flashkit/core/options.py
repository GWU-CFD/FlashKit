"""Define argparse custom actions and some option implementations."""

# type annotations
from __future__ import annotations

# standard libraries
import argparse

# internal libraries
from ..core.configure import force_delayed, get_defaults
from ..core.logging import force_debug, force_debug_console
from ..core.parallel import force_parallel
from ..core.tools import read_a_branch
from ..resources import CONFIG, MAPPING, TEMPLATES

# external libraries
from cmdkit.config import Namespace

# define library (public) interface
__all__ = ['return_available', 'return_commands', 'return_options',
           'DebugLogging', 'ForceDelayed', 'ForceParallel']

# define configuration constants (internal)
MIN_DEF = CONFIG['core']['options']['mindef']
MIN_MAP = CONFIG['core']['options']['minmap']
PAD_DEF = CONFIG['core']['options']['paddef']
PAD_MAP = CONFIG['core']['options']['padmap']

class DebugLogging(argparse.Action):
    """Create custom action for setting debug logging."""
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest):
            force_debug_console()
        else:
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

def return_available(*, category: str, tags: list[str] = [], skips: list[str] = []) -> None:
    """Provide the available library templates for flashkit."""
    print(
            f'The following library template key/value pairs are provided:\n'
            f'with the tags of {tags} defined in each section')
    for section, layout in TEMPLATES[category].items():
        if section in skips: continue
        print(f'\n Section: {section}\n')
        for tag, values in layout.items():
            if not tags or tag in tags:
                if tag in skips: continue
                print(
                    f'Parameter\t{tag}\n'
                    f'---------\t{"-"*len(tag)}')
                print('\n'.join(f'{tmp}\t\t{value}' for tmp, value in values.items()))

def return_commands(*, category: str = 'batch', skips: list[str] = []) -> None:
    """Provide the available library templates for flashkit."""
    print(f'The following library template key/value pairs are provided:')
    for section, layout in TEMPLATES[category].items():
        if section in skips: continue
        number = layout.get('comment', {}).get('number', '')
        print(f'\n Section: {section}  < {number} >\n\n'
              f'Key    (Number)\t\tShell Cmd\n'
              f'---------------\t\t---------')
        print('\n'.join(f'{cmd}\t({val.get("number", "")})\t\t{val.get("value","")} {val.get("source", "")} {val.get("post", "")}'
            for cmd, val in layout.items() if cmd not in skips))
        print('')

def return_options(stem: list[str]) -> None:
    """Provide the defaults and mappings for flashkit <category> <operation>."""
    options = read_a_branch(stem, get_defaults())
    mapping = read_a_branch(stem, MAPPING)
    command = " ".join(stem)
    flatten = lambda value: (value if value != '' else '--') if not isinstance(value, Namespace) else dict(value)
    coldef = max([len(opt) for opt in options] + [MIN_DEF, ]) + PAD_DEF
    colmap = max([len(opt) for opt in mapping] + [MIN_MAP, ]) + PAD_MAP
    defaults = '\n'.join(f'{opt: <{coldef}} {flatten(value)}'
            for opt, value in options.items())
    mappings = '\n\n'.join(f"{opt: <{colmap}} [{'.'.join(path)}]\n{' '*colmap} {gen} = ..."
            for opt, (*path, gen) in mapping.items())
    message = (
        f'The following library defaults are provided for flashkit {command}:\n'
        f'\n'
        f'{"Options": <{coldef}} Default Values\n'
        f'{"-------": <{coldef}} --------------\n'
        f'{defaults}\n'
        f'\n\n'
        f'The following outlines the general section options, which can be mapped\n'
        f'in the configuration file, that are provided for flashkit {command}:\n'
        f'\n'
        f'{"Options": <{colmap}} flash.toml Sections and Options\n'
        f'{"-------": <{colmap}} -------------------------------\n'
        f'{mappings}\n'
        )
    print(message)
