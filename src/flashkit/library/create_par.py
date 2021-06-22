"""Create a FLASH parameters file for running a simulation."""

# type annotations
from __future__ import annotations
from typing import Any, NamedTuple

# standard libraries
import os
from functools import reduce

# internal libraries
from ..core.configure import get_templates, get_defaults
from ..core.parallel import safe, single, squash
from ..resources import CONFIG

# external libraries
import toml

# define library (public) interface
__all__ = ['author_par', 'sort_template', 'write_par', ]

# define configuration constants (internal)
DEF_SECT = CONFIG['create']['par']['local']
PAD_NAME = CONFIG['create']['par']['name']
PAD_NOTE = CONFIG['create']['par']['note']
PAD_SECT = CONFIG['create']['par']['sect']
SENTINAL = CONFIG['create']['par']['sentinal']
FILENAME = CONFIG['create']['par']['filename']
MAX_LVLS = CONFIG['core']['configure']['max']
MAX_TEMP = CONFIG['create']['par']['max']

# define library defaults
DEFAULTS = get_defaults()

@safe
def sort_templates(tmp: list[str], *args) -> int:
    """Define the sorting algorythm to implement template precedence."""
    arg, *_ = args 
    src = 1 if 'sources' in args else 0
    try:
        return src + {'local': -1, 'system': int(MAX_TEMP * MAX_LVLS * 10)}[arg] 
    except KeyError: 
        usr, lvl = arg.split('_')
        return src + int(lvl) + {k: MAX_LVLS * 10 * n for n, k in enumerate(tmp)}[usr]

@single
def author_par(*, templates: dict[str, dict[str, Any]]) -> list[str]:
    """Author a flash.par file from section templates."""
    lines: list[str] = list()
    for section, layout in templates.items():
        lines.extend(author_section(section, layout))
    return lines

@squash
def write_par(*, dest: str, lines: list[str]) -> None:
    """Write the parameter file to destination."""
    with open(os.path.join(dest, FILENAME), 'w') as file:
        for line in lines:
            file.write(line)

def author_section(section: str, layout: dict[str, Any]):
    comment = layout.pop('comment', {})
    header = comment.get('header', section)
    footer = comment.get('footer', None)

    sources = layout.pop('sources', {}) 
    
    params = [(name, value) for name, value in layout.items()]
    params.extend((name, read_a_source(stem, DEFAULTS)) for name, stem in sources.items())

    pad = max((len(name) for name, _ in params), default=0) + PAD_NAME
    lines = [f'# {header}', ]
    lines.extend(
            f'{name: <{pad}} = {value}{fmt_note(comment.get(name, None))}'
            for name, value in params)
    lines.append('' if not footer else f'# {footer}')
    lines.extend('' for _ in range(PAD_SECT))

    return lines

def fmt_note(note: Any) -> str:
    return '' if not note else f"{'#':>{PAD_NOTE}} {note}"

def read_a_source(stem, tree):
    try:
        safe = lambda leaf: leaf if leaf[0] != '_' else int(leaf[1:])
        return reduce(lambda branch, leaf: branch[safe(leaf)], stem, tree)
    except KeyError:
        return None

