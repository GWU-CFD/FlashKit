"""Create a FLASH parameters file for running a simulation."""

# type annotations
from __future__ import annotations
from typing import Any, NamedTuple

# standard libraries
import os
from functools import reduce

# internal libraries
from ..core.configure import get_templates, get_defaults
from ..core.error import LibraryError
from ..core.logging import logger
from ..core.parallel import safe, single, squash
from ..resources import CONFIG
from ..support.types import Lines, Sections, Template

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

# define library defaults
DEFAULTS = get_defaults()

@single
def author_par(*, template: Template) -> Lines:
    """Author a flash.par file from section templates."""
    lines: list[str] = list()
    for section, layout in sorted(template.items(), key=order_sections):
        lines.extend(author_section(section, layout))
    return lines

@safe
def filter_tags(key: str) -> bool:
    """Define the filter function for supported keys."""
    try:
        return key in SUPPORTS or key[0] == SENTINAL
    except IndexError:
        raise LibraryError('Templates do not support empty keys!') 

@safe
def sort_templates(templates: list[str], *args) -> int:
    """Define the sorting algorythm to implement template precedence."""
    (arg, *path), *_ = args
    src = 1 if SOURCING in args else 0
    try:
        return src + {'local': -1, 'system': int(MAX_TEMP * MAX_LVLS * 10)}[arg] 
    except KeyError: 
        usr, lvl = arg.split('_')
        return src + int(lvl) + {k: MAX_LVLS * 10 * n 
                for n, k in enumerate(templates)}[usr]

@squash
def write_par(*, lines: Lines, path: str) -> None:
    """Write the parameter file to destination."""
    with open(os.path.join(path, FILENAME), 'w') as file:
        for line in lines:
            file.write(line + '\n')

def author_section(section: str, layout: Sections):
    comment = layout.pop(TAGGING, {})
    header = comment.get('header', section)
    footer = comment.get('footer', None)

    sources = layout.pop(SOURCING, {}) 
    sinks = layout.pop(SINKING, {})
    
    if not layout and not sources and section != TITLE:
        return list()
    
    params = [(name, value) for name, value in layout.items()]
    params.extend((name, read_a_source(stem, DEFAULTS)) for name, stem in sources.items())

    pad = max((len(name) for name, _ in params), default=0) + PAD_NAME
    lines = [f'# {header}', ]
    lines.extend(
            f'{name: <{pad}} = {value}{fmt_note(comment.get(SENTINAL + name, None))}'
            for name, value in params)
    lines.append('' if not footer else f'# {footer}')
    lines.extend('' for _ in range(PAD_SECT))

    return lines

def fmt_note(note: Any) -> str:
    return '' if not note else f"{'#':>{PAD_NOTE}} {note}"

def order_sections(*args) -> str:
    (section , layout), *_ = args
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

