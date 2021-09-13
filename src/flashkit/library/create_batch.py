"""Create a FLASH job script for running a simulation."""

# type annotations
from __future__ import annotations
from typing import Any 

# standard libraries
from functools import partial

# internal libraries
from ..core.parallel import single, squash
from ..resources import CONFIG
from ..support.template import author_template, order_commands, read_a_source, write_template
from ..support.types import Lines, Sections, Template, Tree

# define library (public) interface
__all__ = ['author_batch', 'write_batch', ]

# define configuration constants (internal)
PAD_SECT = CONFIG['create']['batch']['padsect']
SENTINAL = CONFIG['support']['template']['sentinal']
TAGGING = CONFIG['support']['template']['tagging']
TITLE = CONFIG['support']['template']['title']

@single
def author_batch(*, template: Template, sources: Tree) -> Lines:
    """Author a flash job script from section templates."""
    return author_template(template=template, sources=sources, author=author)

@squash
def write_batch(*, lines: Lines, path: str, name: str) -> None:
    """Write the flash job script to destination."""
    write_template(lines=lines, path=path, filename=name)

def author(section: str, layout: Sections, tree: Tree) -> Lines:
    comment = layout.pop(TAGGING, {})
    header = comment.get('header', section)
    keep = comment.get('keep', section in {TITLE, })
    footer = comment.get('footer', None)
    noheader = comment.get('noheader', False)
    nofooter = comment.get('nofooter', False)

    if not layout and not keep: return list()
   
    commands = [cmd for _, cmd in sorted(layout.items(), key=order_commands)]
    parts = [' '.join(filter(None,
        (fmt_value(cmd), fmt_source(tree, cmd), fmt_post(cmd))
        )) for cmd in commands]
    notes = [fmt_note(cmd) for cmd in commands]
    pad_line = 0 if not parts else len(max(parts, key=len))
    commands = [f'{part: <{pad_line}}  {note}' for part, note in zip(parts, notes)]

    lines = [] if noheader else [f'# {header}', ]
    lines.extend(command for command in commands)
    if not nofooter: 
        lines.append('' if not footer else f'# {footer}')
        lines.extend('' for _ in range(PAD_SECT))

    return lines

def fmt_note(command: dict[str, Any]) -> str:
    note = command.get(SENTINAL, None)
    return '' if note is None else f'# {note}'

def fmt_post(command: dict[str, Any]) -> str:
    post = command.get('post', None)
    return '' if post is None else f'{post}'

def fmt_value(command: dict[str, Any]) -> str:
    value = command.get('value', None)
    return '' if value is None else f'{value}'

def fmt_source(tree: Tree, command: dict[str, Any]) -> str:
    source = read_a_source(command.get('source', []), tree)
    return '' if source is None else f'{source}'
