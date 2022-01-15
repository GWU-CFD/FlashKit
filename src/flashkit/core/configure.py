"""Support for importing config files along directory tree."""

# type annotations
from __future__ import annotations
from typing import Any, Dict, Iterator, NamedTuple, Optional, cast
from collections.abc import MutableMapping

# standard libraries
import logging
import os
import sys
from functools import partial, reduce

# external libraries
import toml
from cmdkit.config import Configuration, Namespace
from cmdkit.contrib.builder import BuilderConfiguration

# internal libraries
from .tools import read_a_leaf
from ..resources import CONFIG, DEFAULTS, MAPPING, TEMPLATES

logger = logging.getLogger(__name__)

# module access and module level @property(s)
THIS = sys.modules[__name__]

# define library (public) interface
__all__ = ['get_arguments', 'get_defaults', 'get_templates']

# define configuration constants
BASE = CONFIG['core']['configure']['base']
FILE = CONFIG['core']['configure']['file']
LABEL = CONFIG['core']['configure']['label']
MAX = CONFIG['core']['configure']['max']
PATH = CONFIG['core']['configure']['path']
ROOT = CONFIG['core']['configure']['root']
USER = CONFIG['core']['configure']['user']
PAD = f'0{len(str(MAX-1))}'

# internal member for forced delayed
_DELAYED: Optional[bool] = None

class Leaf(NamedTuple):
    """Definiton of a tree leaf."""
    leaf: Any
    stem: list[str]

class WalkError(Exception):
    """Raised when there is an issue walking the path."""

def force_delayed(state: bool = True) -> None:
    """Force the assumption of an on import or on call configure state."""
    THIS._DELAYED = state # type: ignore # pylint: disable=protected-access
    logger.debug('Force -- Delayed Configuration!')

def gather(first_step: str = PATH, *, filename: str = FILE, stamp: bool = True) ->  dict[str, dict[str, Any]]:
    """Walk the steps on the path to read the trees of configuration."""
    user = USER if filename == FILE else filename.split('.')[0]
    trees = [(where, tree) for where, tree in walk_the_path(first_step, filename=filename) if tree is not None]
    return {f'{user}_{steps:{PAD}}': dict(tree, **{LABEL: where}) if stamp else dict(tree) for steps, (where, tree) in enumerate(reversed(trees))}

def prepare(trees: MutableMapping[str, Any], book: Optional[MutableMapping[str, Any]] = None) -> dict[str, Namespace]:
    """Prepare all the trees and plant them for harvest, creating a forest."""
    return {where: plant_a_tree(tree, book) for where, tree in trees.items()}

def harvest(*, trees: dict[str, Namespace] = {}, system: Namespace = Namespace(), local: Namespace = Namespace()) -> Configuration:
    """Harvest the fruit of local and system, and the fruit of knowlege from the trees on the path."""
    return Configuration(system=system, **trees, local=local)

def find_the_leaves(tree: Optional[MutableMapping[str, Any]]) -> list[Leaf]:
    """Return the leaves (and their stems) of the tree; bearing their fruits and knowlege."""
    leaves = []
    if tree is not None:
        leaves = [Leaf(read_a_leaf(stem, tree), stem) for stem in walk_the_tree(tree)]
    return leaves

def plant_a_tree(tree: MutableMapping[str, Any], book: Optional[MutableMapping[str, Any]] = None) -> Namespace:
    """Suffle the leaves of the tree using the pages of a book as your guide."""
    plant = Namespace(tree)
    pages = find_the_leaves(book)
    for page in pages:
        leaf = read_a_leaf(page.leaf, tree)
        root = read_a_leaf(page.stem, tree)
        if leaf is not None and root is None:
            for step in reversed(page.stem):
                leaf = {step: leaf}
            plant.update(leaf)
    return plant

def walk_the_path(first_step: str = PATH, *, filename: str = FILE, root: Optional[str] = None) -> Iterator[tuple[str, Optional[MutableMapping[str, Any]]]]:
    """Walk the path, learning from the trees of knowlege (like os.walk, but opposite)"""

    # read the trees on the path of knowlege ...
    tree: Optional[MutableMapping[str, Any]] = None
    try:
        first_step = os.path.realpath(first_step)
        tree = toml.load(os.path.join(first_step, filename))
        if tree is not None: root = tree.get(ROOT, None)
    except PermissionError as error:
        raise WalkError('Unable to walk the path (... of night in pursuit of knowlege?)!')
    except toml.TomlDecodeError as error:
        raise WalkError('Unable to read from the tree (... of good and evil?)!')
    except FileNotFoundError:
        tree = None
    yield first_step, tree

    # have we reached the end of our journey?
    next_step = os.path.realpath(os.path.join(first_step, '..'))
    last_step = None if (root is None) else os.path.realpath(os.path.expanduser(root))
    is_base_step = any(first_step.endswith(f'/{base}') for base in BASE)
    if next_step == first_step or first_step == last_step or is_base_step:
        return

    # walk the path
    for step in walk_the_path(next_step, filename=filename, root=root):
        yield step

def walk_the_tree(tree: MutableMapping[str, Any], stem: list[str] = []) -> list[list[str]]:
    """Return the leaves of the branches."""
    leaves = []
    for branch, branches in tree.items():
        leaf = stem + [branch, ]
        if isinstance(branches, dict):
            leaves.extend(walk_the_tree(branches, leaf))
        else:
            leaves.append(leaf)
    return leaves

# initialize argument factory for commandline routines
TREES = cast(Dict[str, Namespace], None)

def import_trees() -> None:
    """import once the enviorment is setup; responsibility of the api/cli."""
    logger.debug('Configure -- Initalize configuration on import.')
    THIS.TREES = prepare(gather(), MAPPING) # type: ignore 

def get_defaults(*, local: Namespace = Namespace()) -> Configuration:
    """Constructs arguments from local and system defaults.""" 
    logger.debug(f'Configure -- Prepairing to build arguments.')
    return harvest(local=local, **prepare({'system': DEFAULTS}, MAPPING))

def get_arguments(*, local: Namespace = Namespace()) -> Configuration:
    """Constructs arguments from local, user files, and system defaults;
    also provides support for delayed configuration of file sourced arguments
    until the method call occurs, otherwise this happens on module import."""
    if THIS.TREES is None: import_trees() # type: ignore 
    trees = TREES if not _DELAYED else prepare(gather(), MAPPING)
    logger.debug(f'Configure -- Prepairing to build arguments (Delayed was {_DELAYED}).')
    return harvest(local=local, **prepare({'system': DEFAULTS}, MAPPING), trees=trees)

def get_templates(*, local: Namespace = Namespace(), sources: Optional[list[str]] = None, templates: list[str] = []) -> BuilderConfiguration:
    """Initialize template factory for commandline routines.""" 
    trees: dict[str, Namespace] = dict()
    for template in templates:
        trees.update(**prepare(gather(filename=template, stamp=False)))
    logger.debug(f'Configure -- Built a collection of templates from files.')
    
    if sources is not None:
        source, *sections = sources
        system = prepare({'system': {key: value for key, value in TEMPLATES[source].items() if key in sections}})
        logger.debug(f'Configure -- Appended templates with sections from library defaults.')
        return BuilderConfiguration(**system, **trees, local=local)

    return BuilderConfiguration(**trees, local=local)
