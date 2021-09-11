"""Create an flash parameter file using specified templates and sources."""

# type annotations
from __future__ import annotations
from typing import Any, Optional

# standard libraries
import logging
import os
import sys
from functools import partial

# internal libraries
from ...core.configure import get_arguments, get_defaults, get_templates
from ...core.error import AutoError
from ...core.parallel import safe, single, squash
from ...core.progress import attach_context 
from ...core.stream import Instructions, mail
from ...core.tools import read_a_leaf
from ...library.create_par import author_par, write_par
from ...resources import CONFIG, TEMPLATES
from ...support.template import filter_tags, sort_templates
from ...support.types import Template, Tree

# external libraries
from cmdkit.config import Namespace

logger = logging.getLogger(__name__)

# define public interface
__all__ = ['par', ]

# define configuration constants (internal)
FILENAME = CONFIG['create']['par']['filename']
NOSOURCE = CONFIG['create']['par']['nosource']
TEMPLATE = CONFIG['create']['par']['template']
TAGGING = CONFIG['support']['template']['tagging']

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""

    # determine arguments passed
    if args.get('auto', False):
        templates_given = False
        logger.debug(f'api -- Forced auto behavior for templates.')
    else:    
        templates_given = 'templates' in args.keys()
        if not templates_given:
            raise AutoError('Templates must be given, or use --auto.')  
    if args.get('nosources', False):
        sources_given = True
        args['sources'] = list()
        logger.debug(f'api -- Forced ignore behavior for sources.')
    else:
        sources_given = 'sources' in args.keys()
        if not sources_given:
            raise AutoError('Sources must be given, or use --nosources.')

    # resolve proper absolute directory paths
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))
    logger.debug(f'api -- Fully resolved the destination path.')

    # find the templates 
    if not templates_given:
        arguments = get_arguments()
        args['templates'] = list(dict.fromkeys([template 
            for space, paths in reversed(arguments.whereis(TEMPLATE).items())
            for path in paths 
            for template in read_a_leaf([space, TEMPLATE], arguments.namespaces) # type: ignore
            ]))
        logger.debug(f'api -- Identified templates using all configuration files.')

    # find the sources 
    if not sources_given:
        args['sources'] = [source for source in TEMPLATES['parameter'].keys()
                if source not in NOSOURCE]
        logger.debug(f'api -- Used the library default sources.')

    # find the lookup for sources
    args['tree'] = get_defaults() if args.get('ignore', False) else get_arguments()

    # read and combine the templates
    files = [file + '.toml' for file in args['templates']]
    if 'params' in args:
        local = Namespace({'local': args['params']})
        local['local'][TAGGING] = {'header': 'Command Line Provided Parameters'}
        logger.debug(f'api -- Appended local parameters provided.')
    else:
        local = Namespace()
    sources = ['parameter', ] + args['sources']
    construct = get_templates(local=local, sources=sources, templates=files)
    logger.debug(f'api -- Constructed combined templated info.')

    # filter the templates
    if not args.get('duplicates', False):
        construct = construct.trim(filter_tags, key=partial(sort_templates, args['templates']))
        logger.debug(f'api -- Combined template was trimmed.')
    args['construct'] = construct

    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    templates = args['templates']
    sources = args['sources']
    params = list(args.get('params', {}).keys())
    dest = os.path.relpath(args['dest'])
    nofile = ' (no file out)' if args['nofile'] else ''
    message = '\n'.join([
        f'Creating FLASH parameter file by processing the following:',
        f'  templates     = {templates}',
        f'  sources       = {sources}',
        f'  parameters    = {params}',
        f'  output        = {os.path.join(dest, FILENAME)}',
        f'',
        f'Processing templates and authoring par{nofile} ...',
        ])
    logger.info(message)
    return args

# default constants for handling the argument stream
PACKAGES = {'templates', 'params', 'sources', 'dest', 'auto', 'nosources', 'duplicates', 'result', 'nofile'}
ROUTE = ('create', 'par')
PRIORITY = {'ignore', 'cmdline'}
CRATES = (adapt_arguments, attach_context, log_messages)
DROPS = {'ignore', 'auto', 'nosources', 'templates', 'params', 'sources', 'duplicates'}
MAPPING = {'construct': 'template', 'tree': 'sources'}
INSTRUCTIONS = Instructions(packages=PACKAGES, route=ROUTE, priority=PRIORITY, crates=CRATES, drops=DROPS, mapping=MAPPING)

@single
@mail(INSTRUCTIONS)
def process_arguments(**arguments: Any) -> dict[str, Any]:
    """Composition of behaviors intended prior to dispatching to library."""
    return arguments

@squash
def screen_out(*, lines: list[str]) -> None:
    """Output authored parameter file to the screen."""
    print(f'\nThe authored parameter file is as follows:\n')
    for line in lines:
        print(line)

@safe
def par(**arguments: Any) -> Optional[Any]:
    """Python application interface for using templates to create a FLASH runtime parameter file.

    This method creates a FLASH parameter file (INI format) using options and specified templates
    implemented in toml files to enable runtime context to the creation of parameter files. This
    supports improved consitancy, reproducability, and confidence in research. Additionally, the
    intent is to preserve human readability of the produced FLASH parameter file.

    Keyword Arguments:
        templates (list):   Specify a list of template files (e.g., rayleigh) to search for, without the
                            '.toml' extension. These will be combined and used to create the flash.par file.
        params (dict):      Specific parameters; which are collected in a section at the end of the parameter file.
        sources (list):     Which library defined sourced parameter templates to use (use --available to see options).
        dest (str):         Path to parameter file.
        auto (bool):        Force use of all templates specified in all configuration files.
        nosources (bool):   Do not use any library specified sourced parameter templates.
        duplicates (bool):  Allow the writing of duplicate parameters if there are multiple matches.
        nofile (bool):      Do not write the assembled parameters to file.
        result (bool):      Return the formated and assembled parameters. 
        ignore (bool):      Ignore configuration file provided arguments, options, and flags.

    Notes:  
        If duplicates are not allowed, only the most significant instance of a parameter will be written to
        the parameter file, which means the parameter will be based on the depth-first-merge of all relavent 
        templates and resolved sources from defaults, configuration files, and provided options.

        The order of precedence for parameters with potential duplicate entries in ascending order is.
          0) depth-first-merge of defaults, configuration files, and provided options; resolution of sourced parameters,
          1) parameters retrieved from specified library default parameter templates,
          2) duplicate parameters of the same type in the same template file are ignored,
          3) duplicate parameters of different types in the same template file are ordered as sinked < sourced < explicite 
          4) duplicate parameters of any type in different template files within the same folder are orderd as the specified templates,
          5) duplicate parameters of any type in any template files from a deeper folder in the folder tree,
          6) explicite parameters provided at the command line.
    """
    args = process_arguments(**arguments)
    path = args.pop('dest')
    result = args.pop('result')
    nofile = args.pop('nofile')
    cmdline = args.pop('cmdline', False)
    
    with args.pop('context')() as progress:
        lines = author_par(**args)
        if not nofile: write_par(lines=lines, path=path)
    
    if not result: return None
    if cmdline: screen_out(lines=lines)
    return lines
