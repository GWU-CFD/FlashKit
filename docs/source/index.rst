FlashKit
========

A python based sdk and simple command line interface to assist researchers in using the FLASH code.

.. image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square
    :target: https://opensource.org/licenses/MIT
    :alt: License

.. image:: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue?style=flat-square&logo=python
    :target: https://python.org
    :alt: Python Versions

.. image:: https://img.shields.io/badge/requires-numpy%20%7C%20h5py%20%7C%20toml%20%7C%20cmdkit%20%7C%20psutil-blue?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/network/dependencies
    :alt: Dependancy

.. image:: https://img.shields.io/github/v/release/GWU-CFD/FlashKit?include_prereleases&style=flat-square&logo=github
    : target: https://github.com/GWU-CFD/FlashKit
    :alt: Release

|

The *FlashKit* library implements a useful set of abstractions to common operations reseachers perform when using the
FLASH software, which are avalable from either the command line or python code with a consitant user interface. The
behaviors of these operations are adaptable to the specific needs of the researcher. In particular, *FlashKit* uses
configuration files within a folder hierarchy of simulations to implement a dynamic and reproducable behavior based
on the location of execution to maximize productivity and confidence.

--------------------

Features
--------

The *FlashKit* library provides a number of useful operations for a FLASH user, which fall into several categories.
These are accessed in a very natural way by specifying the catagory and operations desired. Specifically, an operation
is an inteded task such as a pre- or post-processing action and catagories are collections of related operations. In 
this way the command line interface can provide a very 'natural language' interface to the user.

A this time, the inteded scope of the *FlashKit* library looks like the following, 
where the clouds indicate functions that are under development but are not yet complete.

.. image:: /_static/Commands.png
    :alt: FlashKit Commands

|

These operations are available from the command line using::

    flashkit category operation <option> <value> <flag> ...

They are also available from python code using the following interface:

.. code-block:: python

    from flashkit import flash
    
    ...

    flash.category.operation(option=value, flag=True, ...)

There are a few minor differences in the command line and python interfaces, these are documented.

--------------------

Installation
------------

If you already have python 3.7 (or greater) installed on your system, you can install *FlashKit* on your system. 
*FlashKit* depends on a number of required (e.g., numpy and h5py) and optional (e.g., mpi4py and alive-progress) libraries; 
these will automatically be installed when you install *FlashKit* if they are already not in your enviornment.

Run the following command to retrieve and install the *FlashKit* library::

    git clone git@github.com:GWU-CFD/FlashKit.git
    pip install -e FlashKit

You should now be able to run *FlashKit* from the command line or from within your python code.

--------------------

Getting Started
---------------

The :ref:`introduction<introduction>` walkthrough is the right place to start if you are new to *FlashKit*.

You can also checkout the following detailed guides for understanding all of the available functionality of *FlashKit*:

.. toctree::

    tutorial/index

Full documentation of the application programing interface (API) for *FlashKit* is available as well.
You should consult this documentation with specific questions conderning how specific operations will behave
and what available options they provide. Finally, a complete listing of avaialble configuration file options
and template file specifications are also available.

.. toctree::
    :maxdepth: 2

    api/index
    cmdline
    configure
    templates

--------------------

Development Status
------------------

| Issues 

.. image:: https://img.shields.io/github/issues/GWU-CFD/FlashKit?style=flat-square 
    :target: https://github.com/GWU-CFD/FlashKit/issues
    :alt: Issues

.. image:: https://img.shields.io/github/issues/GWU-CFD/FlashKit/bug?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/labels/bug
    :alt: Bug

.. image:: https://img.shields.io/github/issues/GWU-CFD/FlashKit/enhancement?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/labels/enhancement
    :alt: Enhancement

.. image:: https://img.shields.io/github/issues/GWU-CFD/FlashKit/cleanup?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/labels/cleanup
    :alt: Cleanup

| Progress

.. image:: https://img.shields.io/github/milestones/progress/GWU-CFD/FlashKit/1?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22Framework+Complete%22
    :alt: Framework Complete

.. image:: https://img.shields.io/github/milestones/progress/GWU-CFD/FlashKit/2?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22Create+Tools%22
    :alt: Create Tools

.. image:: https://img.shields.io/github/milestones/progress/GWU-CFD/FlashKit/5?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22Documentation+Complete%22
    :alt: Documentation Complete

.. image:: https://img.shields.io/github/milestones/progress/GWU-CFD/FlashKit/6?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22Testing+Complete%22   
    :alt: Testing Complete

.. image:: https://img.shields.io/github/milestones/open/GWU-CFD/FlashKit?style=flat-square
    :target: https://github.com/GWU-CFD/FlashKit/milestones
    :alt: Milestones

|

If you are interested in helping provide new functionality for *FlashKit*, or otherwise would like to identify issues
with the library or lack of clarity in documentation, please consult both the :ref:`contributions<Contributing>` and 
:ref:`adding new features<Adding New Features>` discussion of this documentation.

--------------------

.. toctree::
    :hidden:

    contributing
    license
