"""Create an flash parameter file using specified templates and sources."""

# type annotations
from __future__ import annotations
from typing import Any, Optional

# standard libraries
import logging
import os
import re

# internal libraries
from ...core.configure import get_arguments, get_defaults, get_templates
from ...core.error import AutoError
from ...core.parallel import safe, single, squash
from ...core.parse import ListStr
from ...core.progress import attach_context 
from ...core.stream import Instructions, mail
from ...core.tools import read_a_leaf
from ...library.create_batch import author_batch, write_batch
from ...resources import CONFIG
from ...support.template import write_a_source

# external libraries
from cmdkit.config import Namespace

logger = logging.getLogger(__name__)

# define public interface
__all__ = ['batch', ]

# define configuration constants (internal)
BINARY = CONFIG['build']['simulation']['binary']
TEMPLATE = CONFIG['create']['batch']['template']
PARAFILE = CONFIG['create']['par']['filename']

def adapt_arguments(**args: Any) -> dict[str, Any]:
    """Process arguments to implement behaviors; will throw if some defaults missing."""
   
    # ensure arguments provided
    if any(arg not in args for arg in {'job', 'build'}):
        raise AutoError('Both job and build arguments are required!')
    
    # determine arguments passed
    if args.get('auto', False):
        bname_given = False
        logger.debug(f'Application -- Forced auto behavior for basename.')
    else:    
        bname_given = 'basename' in args.keys()
        if not bname_given: raise AutoError('Basename must be given, or use --auto.')  
    if args.get('find', False):
        templates_given = False
        logger.debug(f'Application -- Forced find behavior for templates.')
    else:
        if 'templates' in args.keys():
            templates_given = True
        elif args.get('auto', False) and 'basename' in args.keys():
            templates_given = True
            args['templates'] = ListStr(args.pop('basename'))
        else: 
            raise AutoError('Templates must be given, or use --find.')  
    if args.get('nosources', False):
        args['sources'] = list()
        logger.debug(f'Application -- Forced ignore behavior for sources.')

    # resolve proper absolute directory paths
    args['path'] = os.path.realpath(os.path.expanduser(args['path']))
    args['dest'] = os.path.realpath(os.path.expanduser(args['dest']))
    args['source'] = os.path.realpath(os.path.expanduser(args['source']))
    logger.debug(f'Application -- Fully resolved the source and destination paths.')
    
    # prepare conditions in order to arrange a list of files to process
    str_include = re.compile(args['plot'])
    str_exclude = re.compile(args['force'])
    if not bname_given:
        listdir = os.listdir(args['path'])
        condition = lambda file: re.search(str_include, file) and not re.search(str_exclude, file)

    # create the basename; if guessing, try multiple methods
    if not bname_given:
        try:
            args['basename'], *_ = next(filter(condition, (file for file in listdir))).split(str_include.pattern)
        except StopIteration:
            try:
                file = open(PARAFILE).read()
                found = re.search('basenm *=.*\n', file)
                if found: args['basename'] = found.group().split('\"')[1].rstrip('_')
            except (AttributeError, FileNotFoundError, IndexError):
                raise AutoError(f'Cannot automatically parse basename for simulation files on path {args["path"]}')

    # find the templates, if searching 
    if not templates_given:
        arguments = get_arguments()
        args['templates'] = list(dict.fromkeys([template 
            for space, paths in reversed(arguments.whereis(TEMPLATE).items())
            for path in paths 
            for template in read_a_leaf([space, TEMPLATE], arguments.namespaces) # type: ignore
            ]))
        logger.debug(f'Application -- Identified templates using all configuration files.')

    # identify the build directory from user input
    ndim = max(min(3, args['ndim']), 2)
    nxb, nyb, nzb = (args[b] for b in ('nxb', 'nyb', 'nzb'))
    grid = {'paramesh': 'pm4dev', 'uniform': 'ug', 'regular': 'rg'}.get(args['grid'], args['grid'].strip('-+'))
    build = f"{grid}{args['build']}_{ndim}D{nxb}_{nyb}" + ('' if ndim == 2 else f'_{nzb}')
    
    # specify the shell script and redirected output filenames
    args['filename'] = f'{args["basename"]}{args["batch"]}.run'
    redirect = f'{args["basename"]}{args["out"]}.out'
    
    # construct the computed arguments
    iprocs, jprocs, kprocs = (args[b] for b in ('iprocs', 'jprocs', 'kprocs'))
    nprocs = int(iprocs * jprocs * kprocs)
    ntasks = int(args['ntasks'])
    nnodes = max(1, int(nprocs / ntasks))
    
    # construct the run argument
    run = args['launch']
    if not args.get('notasks', False): run = f'{run} -n {nprocs}'
    if args.get('hostfile', False): run = f'{run} --hostfile {args["hosts"]}'
    run = f'{run} {os.path.join(args["source"], build, BINARY)}'
    if args.get('redirect', False): run = f'{run} > {redirect}'
    if args.get('screen', False): run = f"screen -d -m -S {args['job']} bash -c \'{run}\'"
        
    # find the lookup for sources and append with computed arguments
    tree = get_defaults() if args.get('ignore', False) else get_arguments()
    write_a_source(['create', 'batch', 'job'], tree, args['job'])
    write_a_source(['create', 'batch', 'run'], tree, run)
    write_a_source(['create', 'batch', 'nnodes'], tree, nnodes)
    write_a_source(['create', 'batch', 'nprocs'], tree, nprocs)
    write_a_source(['create', 'batch', 'ntasks'], tree, ntasks)
    args['tree'] = tree

    # read and combine the templates
    files = [file + '.toml' for file in args['templates']]
    sources = ['batch', ] + args['sources']
    args['construct'] = get_templates(local=Namespace(), sources=sources, templates=files)
    logger.debug(f'Application -- Constructed combined templated info.')
    return args

def log_messages(**args: Any) -> dict[str, Any]:
    """Log screen messages to logger; will throw if some defaults missing."""
    templates = args['templates']
    sources = args['sources']
    dest = os.path.relpath(args['dest'])
    output = os.path.join(dest, args['filename'])
    nofile = ' (no file out)' if args['nofile'] else ''
    message = '\n'.join([
        f'\nCreating FLASH parameter file by processing the following:',
        f'  templates     = {templates}',
        f'  sources       = {sources}',
        f'  batch_file    = {output}',
        f'',
        f'Processing templates and authoring batch{nofile} ...',
        ])
    logger.info(message)
    return args

# default constants for handling the argument stream
PACKAGES = {'job', 'build', 'basename', 'templates', 'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'ntasks',
            'grid', 'source', 'launch', 'sources', 'path', 'dest', 'hosts', 'plot', 'force', 'batch', 'out',
            'auto', 'find', 'redirect', 'screen', 'hostfile', 'notasks', 'nosources', 'nofile', 'result'}
ROUTE = ('create', 'batch')
PRIORITY = {'ignore', 'cmdline'}
CRATES = (adapt_arguments, attach_context, log_messages)
DROPS = {'job', 'build', 'basename', 'templates', 'ndim', 'nxb', 'nyb', 'nzb', 'iprocs', 'jprocs', 'kprocs', 'ntasks',
         'grid', 'source', 'launch', 'sources', 'path', 'hosts', 'plot', 'force', 'batch', 'out', 'ignore', 
         'auto', 'find', 'redirect', 'screen', 'hostfile', 'notasks', 'nosources'}
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
def batch(**arguments: Any) -> Optional[Any]:
    args = process_arguments(**arguments)
    path = args.pop('dest')
    name = args.pop('filename')
    result = args.pop('result')
    nofile = args.pop('nofile')
    cmdline = args.pop('cmdline', False)
    
    with args.pop('context')() as progress:
        lines = author_batch(**args)
        if not nofile: write_batch(lines=lines, path=path, name=name)
    
    if not result: return None
    if cmdline: screen_out(lines=lines)
    return lines
