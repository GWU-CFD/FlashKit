"""Create a FLASH parameters file for running a simulation."""

# type annotations
from __future__ import annotations
from typing import Any 

# internal libraries
from ..core.parallel import single, squash
from ..resources import CONFIG
from ..support.template import author_template, read_a_source, write_template
from ..support.types import Lines, Sections, Template, Tree

# define library (public) interface
__all__ = ['author_par', 'write_par', ]

# define configuration constants (internal)
FILENAME = CONFIG['create']['par']['filename']
PAD_NAME = CONFIG['create']['par']['padname']
PAD_NOTE = CONFIG['create']['par']['padnote']
PAD_SECT = CONFIG['create']['par']['padsect']
SENTINAL = CONFIG['support']['template']['sentinal']
SINKING = CONFIG['support']['template']['sinking']
SOURCING = CONFIG['support']['template']['sourcing']
TAGGING = CONFIG['support']['template']['tagging']
TITLE = CONFIG['support']['template']['title']

@single
def author_par(*, template: Template, sources: Tree) -> Lines:
    """Author a flash.par file from section templates."""
    return author_template(template=template, sources=sources, author=author)

@squash
def write_par(*, lines: Lines, path: str) -> None:
    """Write the parameter file to destination."""
    write_template(lines=lines, path=path, filename=FILENAME)

def author(section: str, layout: Sections, tree: Tree) -> Lines:
    comment = layout.pop(TAGGING, {})
    header = comment.get('header', section)
    keep = comment.get('keep', section in {TITLE, })
    footer = comment.get('footer', None)
    noheader = comment.get('noheader', False)
    sort = comment.get('sorted', False)

    sources = layout.pop(SOURCING, {}) 
    sinks = layout.pop(SINKING, {})
    
    if not layout and not keep and not sources:
        return list()
    
    if sort:
        params = [(name, value) for name, value in sorted(layout.items())]
    else:
        params = [(name, value) for name, value in layout.items()]
    
    params.extend((name, read_a_source(stem, tree)) for name, stem in sources.items())

    pad_name = max((len(name) for name, _ in params), default=0) + PAD_NAME
    pad_value = max((len(str(value)) for _, value in params), default=0) + PAD_NOTE
    lines = [] if noheader else [f'# {header}', ]
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
