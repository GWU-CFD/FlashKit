"""Support for importing config files along directory tree.""" 

# type annotations
from __future__ import annotations
from typing import Any, Dict, List, NamedTuple, Optional

# standard libraries
import os
from functools import reduce

# internal libraries
from ...resources import CONFIG, DEFAULTS, MAPPING

# external libraries
import toml
from cmdkit.config import Configuration, Namespace

# default constants
PATH = CONFIG['core']['configure']['path']
BASE = CONFIG['core']['configure']['base']
FILE = CONFIG['core']['configure']['file']
ROOT = CONFIG['core']['configure']['root']
USER = CONFIG['core']['configure']['user']
LABEL = CONFIG['core']['configure']['label']
MAX = CONFIG['core']['configure']['max']
PAD = f'0{len(str(MAX))}'

class Leaf(NamedTuple):
    """Definiton of a tree leaf."""
    leaf: Any
    stem: List[str]

class WalkError(Exception):
    """Raised when there is an issue walking the path.""" 

def gather(first_step: str = PATH) -> Dict[str, Dict[str, Any]]:
    """Walk the steps on the path to read the trees of configuration."""
    trees = [(where, tree) for where, tree in walk_the_path(first_step) if tree is not None]
    return {f'{TREE}_{steps:{PAD}}': dict(tree, **{LABEL: where}) for steps, (where, tree) in enumerate(reversed(trees))}

def prepare(trees: Dict[str, Dict[str, Any]], book: Optional[Dict[str, Any]] = None) -> Dict[str, Namespace]:
    """Prepare all the trees and plant them for harvest, creating a forest."""
    return {where: plant_a_tree(tree, book) for where, tree in trees.items()}
                
def harvest(*, trees: Dict[str, Dict[str, Any]] = {}, system: Dict[str, Any] = {}, local: Dict[str, Any] = {}) -> Configuration:
    """Harvest the fruit of local and system, and the fruit of knowlege from the trees on the path."""
    return Configuration(system=system, **trees, local=local)

def find_the_leaves(tree: Dict[str, Any]) -> Dict[str, List[str]]:
    """return the leaves (and their stems) of the tree."""
    leaves = []
    if tree is not None:
        leaves = [Leaf(read_a_leaf(stem, tree), stem) for stem in walk_the_tree(tree)]
    return leaves

def plant_a_tree(tree: Dict[str, Any], book: Optional[Dict[str, Any]] = None) -> Namespace:
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

def read_a_leaf(stem: List[str], tree: Dict[str, Any]) -> Optional[Any]:
    """Read the leaf at the end of the stem on the treee."""
    try:
        return reduce(lambda branch, leaf: branch[leaf], stem, tree) 
    except KeyError:
        return None

def walk_the_path(first_step: str = PATH, root: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Walk the path, learning from the trees of knowlege (like os.walk, but opposite)"""

    # read the trees on the path of knowlege ...
    try:
        first_step = os.path.realpath(first_step)
        tree = toml.load(os.path.join(first_step, FILE))
        root = tree.get(ROOT, None)
    except PermissionError as error:
        print(error)
        raise WalkError('Unable to walk the path (... of night in pursuit of knowlege?)!')
    except toml.TomlDecodeError as error:
        print(error)
        raise WalkError('Unable to read from the tree (... of good and evil?)!')
    except FileNotFoundError:
        tree = None
    yield first_step, tree
    
    # have we reached the end of our journey?
    next_step = os.path.realpath(os.path.join(first_step, '..'))
    last_step = None if (root is None) else os.path.realpath(os.path.expanduser(root))
    if next_step == first_step or first_step == last_step or first_step.endswith(f'/{BASE}'):
        return
    
    # walk the path
    for step in walk_the_path(next_step, root):
        yield step

def walk_the_tree(tree: Dict[str, Any], stem: List[str] = []) -> List[List[str]]:
    """Return the leaves of the branches."""
    leaves = []
    for branch, branches in tree.items():
        leaf = stem + [branch, ]
        if isinstance(branches, dict):
            leaves.extend(walk_the_tree(branches, leaf))
        else:
            leaves.append(leaf)
    return leaves

