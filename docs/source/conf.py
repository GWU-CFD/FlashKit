# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
import datetime
sys.path.insert(0, os.path.abspath('../..'))

# automatic metadata access
from flashkit import __meta__


# -- Project information -----------------------------------------------------

project = 'flashkit'
copyright = f'2021-{datetime.datetime.now().year} Aaron Lentner'
author = f'{__meta__.__authors__} <{__meta__.__contact__}>'

# The full version, including alpha/beta/rc tags
release = __meta__.__version__
version = __meta__.__version__


# -- General configuration ---------------------------------------------------

extensions = [
        'sphinx.ext.autosectionlabel',
        'sphinx.ext.autodoc',
        'sphinx.ext.napoleon',
        'sphinx.ext.mathjax',
        'sphinx.ext.githubpages',
        'sphinx.ext.intersphinx',
        'sphinxcontrib.programoutput',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# do not include fully qualified names of objects with autodoc
add_module_names = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_book_theme'
html_title = ''
html_logo = '_static/logo.png'
html_static_path = ['_static']
html_theme_options = {
        'external_links': [],
        'github_url': 'https://github.com/GWU-CFD/FlashKit',
        }


# -- Extension configuration -------------------------------------------------

intersphinx_mapping = {'https://docs.python.org/3/': None}

# export variables with epilogue
rst_epilog = f"""
.. |release| replace:: {release}
.. |copyright| replace:: {copyright}
"""
