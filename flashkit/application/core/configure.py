"""Support for importing config files along directory tree.""" 

# type annotations
from __future__ import annotations
from typing import Any, Dict

# standard libraries
import os

# internal libraries
from ...resources import CONFIG, DEFAULTS 

# external libraries
import toml
from cmdkit.config import Configuration, Namespace

# default constants
PATH = DEFAULTS['general']['paths']['working']
ROOT = CONFIG['core']['configure']['root']
FILE = CONFIG['core']['configure']['file']
LABEL = CONFIG['core']['configure']['label']
MAX = CONFIG['core']['configure']['max']
PAD = f'0{len(str(MAX))}'

class WalkError(Exception):
    """Raised when there is an issue walking the path.""" 

def gain_config(*, tree: Dict[str, Dict[str, Any]] = {}, system: Dict[str, Any] = {}, local: Dict[str, Any] = {}):
    """Construct the configuration using the fruit of local and system, and knowlege of the tree of configuration."""
    return Configuration(system=system, **{label: Namespace(text) for label, text in tree.items()}, local=local)

def plant_a_tree(bottom: str = PATH):
    """Walk the path of directories to obtain the tree of configuration."""
    raw = [(path, text) for path, text in walk_the_path(bottom) if text is not None]
    return {f'user_{level:{PAD}}': dict(text, **{LABEL: path}) for level, (path, text) in enumerate(reversed(raw))}

def walk_the_path(bottom: str = PATH):
    """Walk the path, emiting fruit and knowlege of the tree of configuration (like os.walk, but opposite)"""

    # read the text on the path of configuration ...
    try:
        bottom = os.path.realpath(bottom)
        text = toml.load(os.path.join(bottom, FILE))
    except PermissionError as error:
        print(error)
        raise WalkError('Unable to walk the path (... of darkness?)!')
    except toml.TomlDecodeError as error:
        print(error)
        raise WalkError('Unable to read the text (... of prophecy?)!')
    except FileNotFoundError:
        text = None
    yield bottom, text
    
    # have we reached the end of our journey?
    new_path = os.path.realpath(os.path.join(bottom, '..'))
    if new_path == bottom or bottom.endswith(f'/{ROOT}'):
        return
    
    # walk the path
    for x in walk_the_path(new_path):
        yield x
