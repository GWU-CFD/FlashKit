"""Create a FLASH job script for running a simulation."""

# type annotations
from __future__ import annotations

# internal libraries
from ..core.parallel import single, squash
from ..resources import CONFIG
from ..support.template import author_template, order_commands, read_a_source, write_template
from ..support.types import Lines, Sections, Template, Tree

# define library (public) interface
__all__ = ['author_batch', 'write_batch', ]

# define configuration constants (internal)
FILENAME = CONFIG['create']['batch']['filename']
PAD_SECT = CONFIG['create']['batch']['padsect']
TAGGING = CONFIG['support']['template']['tagging']
TITLE = CONFIG['support']['template']['title']

@single
def author_batch(*, template: Template, sources: Tree) -> Lines:
    """Author a flash job script from section templates."""
    return author_template(template=template, sources=sources, author=author)

@squash
def write_batch(*, lines: Lines, path: str) -> None:
    """Write the flash job script to destination."""
    write_template(lines=lines, path=path, filename=FILENAME)

def author(section: str, layout: Sections, tree: Tree) -> Lines:
    comment = layout.pop(TAGGING, {})
    header = comment.get('header', section)
    keep = comment.get('keep', section in {TITLE, })
    footer = comment.get('footer', None)
    noheader = comment.get('noheader', False)

    if not layout and not keep:
        return list()
   
    params = [(
        cmd.get('value', ''),
        read_a_source(cmd.get('source', []), tree),
        cmd.get('post', ''),
        cmd.get('_', '')
        ) for name, cmd in sorted(layout.items(), key=order_commands)]

    lines = [] if noheader else [f'# {header}', ]
    lines.extend(' '.join(str(par) for par in param if par) for param in params)
    lines.append('' if not footer else f'# {footer}')
    lines.extend('' for _ in range(PAD_SECT))

    return lines

