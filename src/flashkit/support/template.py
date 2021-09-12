"""Support methods provided for template based file creation."""

# type annotations
from __future__ import annotations
from typing import NamedTuple, Callable

# standard libraries
import os
from functools import reduce

# internal libraries
from ..core.error import LibraryError
from ..resources import CONFIG
from ..support.types import Lines, Sections, Template, Tree

# external libraries
import toml

# define library (public) interface
__all__ = ['author_template', 'filter_tags', 'sort_templates', 'order_sections', 
           'read_a_source', 'write_a_source', 'write_template', ]

# define configuration constants (internal)
MAX_LVLS = CONFIG['core']['configure']['max']
MAX_TEMP = CONFIG['support']['template']['filemax']
SENTINAL = CONFIG['support']['template']['sentinal']
SINKING = CONFIG['support']['template']['sinking']
SOURCING = CONFIG['support']['template']['sourcing']
SUPPORTS = CONFIG['support']['template']['supports']
TAGGING = CONFIG['support']['template']['tagging']
TITLE = CONFIG['support']['template']['title']

def author_template(*, template: Template, sources: Tree,
                    author: Callable[[str, Sections, Tree], Lines]) -> Lines:
    """Author a template file from sections using an author method."""
    lines: list[str] = list()
    for section, layout in sorted(template.items(), key=order_sections):
        lines.extend(author(section, layout, sources))
    return lines

def filter_tags(key: str) -> bool:
    """Define the filter function for supported keys."""
    try:
        return key in SUPPORTS or key[0] == SENTINAL
    except IndexError:
        raise LibraryError('Templates do not support empty keys!') 

def sort_templates(templates: list[str], *args) -> int:
    """Define the sorting algorythm to implement template precedence."""
    (arg, *path), *_ = args
    src = 2 * int(SOURCING in path) + int(SINKING in path) + 1
    try:
        return src + {'local': 0, 'system': int(10 * MAX_TEMP * MAX_LVLS)}[arg]
    except KeyError:
        try:
            tmp, lvl = arg.split('_')
            return src + 10 * templates.index(tmp) + 10 * MAX_TEMP * (MAX_LVLS - (int(lvl) + 1))
        except ValueError:
            raise LibraryError(f'Unknown template name, {tmp}, during sorting!')

def order_commands(*args) -> str:
    """Order the template commands according to the proper tag."""
    (name, command), *_ = args
    try:
        number = command.get('number')
        key = f'{number:03}'
    except KeyError:
        key = name
    except ValueError:
        raise LibraryError(f'Entry number for command {name} is not int!')
    finally:
        return key

def order_sections(*args) -> str:
    """Order the template sections according to the proper tag."""
    (section, layout), *_ = args
    try:
        number = {TITLE: -30, 'local': -50}.get(section, None)
        if number is None: number = layout[TAGGING]['number']
        key = f'{int(number):03}'
    except KeyError:
        key = section
    except ValueError:
        raise LibraryError(f'Entry number for section {section} is not int!')
    finally:
        return key

def read_a_source(stem, tree):
    try:
        if not stem: return None
        safe = lambda leaf: leaf if leaf[0] != SENTINAL else int(leaf[1:])
        return reduce(lambda branch, leaf: branch[safe(leaf)], stem, tree)
    except KeyError:
        return None

def write_a_source(stem, tree, value):
    try:
        path, key = stem if stem[-1][0] != SENTINAL else (*stem[:-1], int(stem[-1][1:]))
        reduce(lambda branch, leaf: branch[leaf], path, tree)[key] = value
    except (KeyError, IndexError):
        raise LibraryError(f'No source found at path {stem}')

def write_template(*, lines: Lines, path: str, filename: str) -> None:
    """Write the template file to destination."""
    with open(os.path.join(path, filename), 'w') as file:
        for line in lines:
            file.write(line + '\n')
