"""Create a FLASH parameters file for running a simulation."""

# type annotations
from __future__ import annotations
from typing import Any, NamedTuple, Callable

# standard libraries
import os
from functools import reduce

# internal libraries
from ..core.error import LibraryError
from ..core.parallel import safe, single, squash
from ..resources import CONFIG
from ..support.types import Lines, Sections, Template, Tree

# external libraries
import toml

# define library (public) interface
__all__ = ['author_par', 'filter_tags', 'sort_templates', 'write_par', ]

# define configuration constants (internal)
MAX_LVLS = CONFIG['core']['configure']['max']
MAX_TEMP = CONFIG['create']['par']['filemax']
FILENAME = CONFIG['create']['par']['filename']
PAD_NAME = CONFIG['create']['par']['padname']
PAD_NOTE = CONFIG['create']['par']['padnote']
PAD_SECT = CONFIG['create']['par']['padsect']
SENTINAL = CONFIG['create']['par']['sentinal']
SUPPORTS = CONFIG['create']['par']['supports']
TAGGING = CONFIG['create']['par']['tagging']
SOURCING = CONFIG['create']['par']['sourcing']
SINKING = CONFIG['create']['par']['sinking']
TITLE = CONFIG['create']['par']['title']
LOCAL = CONFIG['create']['par']['local']

@single
def author_par(*, template: Template, sources: Tree) -> Lines:
    """Author a flash.par file from section templates."""
    lines: list[str] = list()
    for section, layout in sorted(template.items(), key=order_sections):
        lines.extend(author_section(section, layout, sources))
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
    src = 1 if SOURCING in args else 0
    try:
        return src + {'local': -1, 'system': int(MAX_TEMP * MAX_LVLS * 10)}[arg] 
    except KeyError: 
        usr, lvl = arg.split('_')
        return src + MAX_LVLS - int(lvl) + {k: MAX_LVLS * 10 * n 
                for n, k in enumerate(templates)}[usr]

@squash
def write_par(*, lines: Lines, path: str) -> None:
    """Write the parameter file to destination."""
    with open(os.path.join(path, FILENAME), 'w') as file:
        for line in lines:
            file.write(line + '\n')

def author_section(section: str, layout: Sections, tree: Tree):
    comment = layout.pop(TAGGING, {})
    header = comment.get('header', section)
    footer = comment.get('footer', None)
    sort = comment.get('sorted', False)

    sources = layout.pop(SOURCING, {}) 
    sinks = layout.pop(SINKING, {})
    
    if not layout and not sources and section != TITLE:
        return list()
    
    if sort:
        params = [(name, value) for name, value in sorted(layout.items())]
    else:
        params = [(name, value) for name, value in layout.items()]
    
    params.extend((name, read_a_source(stem, tree)) for name, stem in sources.items())

    pad_name = max((len(name) for name, _ in params), default=0) + PAD_NAME
    pad_value = max((len(str(value)) for _, value in params), default=0) + PAD_NOTE
    lines = [f'# {header}', ]
    lines.extend(f'{fmt_name(name, pad_name)}= {fmt_value(value, pad_value)}{fmt_note(name, comment)}'
            for name, value in params)
    lines.append('' if not footer else f'# {footer}')
    lines.extend('' for _ in range(PAD_SECT))

    return lines

def fmt_name(name: str, pad: int) -> str:
    return f'{name: <{pad}}'

def fmt_note(name:str, comment: dict[str, Any]) -> str:
    note = comment.get(SENTINAL + name, None)
    return '' if note is None else f'# {note}'

def fmt_value(value: Any, pad: int) -> str:
    return {bool: f'''{f".{str(value).lower()}.": <{pad}}''',
            str: f'''{f'"{value}"': <{pad}}''',
            }.get(type(value), f'{value: <{pad}}')

def order_sections(*args) -> str:
    (section, layout), *_ = args
    try:
        return str({TITLE: -1, LOCAL: -2}[section])
    except KeyError:
        return str(layout.get(TAGGING, {}).get('number', section))

def read_a_source(stem, tree):
    try:
        safe = lambda leaf: leaf if leaf[0] != SENTINAL else int(leaf[1:])
        return reduce(lambda branch, leaf: branch[safe(leaf)], stem, tree)
    except KeyError:
        return None

def write_a_source(stem, tree, value):
    try:
        path, key = stem if stem[-1][0] != SENTINAL else (*stem[:-1], int(stem[-1][1:]))
        reduce(lambda branch, leaf: branch[leaf], path, tree)[key] = value
    except KeyError, IndexError:
        raise LibraryError(f'No source found at path {stem}')

