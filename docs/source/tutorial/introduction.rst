Introduction
============

Welcome to FlashKit 101
-----------------------

We are going to cover a number of topics from installation to use of configuration files.

Outline

#. Installation of FlashKit
#. Ways to use FlashKit
#. Using the FlashKit create tools
#. Configuration Files
#. The FlashKit python interface

More detailed information is available in subsequent tutorials and the api documentation.

--------------------

Let's get started
-----------------

In order to install and use FlashKit, you at least need python 3.7 or above.

Run the following commands to retrieve and install the FlashKit library::

    cd <path to install location>
    git clone git@github.com:GWU-CFD/FlashKit.git
    pip install -e FlashKit

The '-e' option in the installation line allows us to update the local git repository with
the ``git pull`` command, such as when there is a new release of FlashKit, without reinstalling 
the repository each and every time we would like to update the repository.

If you have difficulty cloning the repository, make sure you both have access to FlashKit and
that your ssh key settings are properly configured with github for the machine you are using.

--------------------

What's there for us
-------------------

There are a number of ways to interact with the FlashKit library.

* Commandline
* Commandline with config files
* Python code

The first and foremost intended use of the FlashKit library is from the commandline, with or without using configuation
files. FlashKit can also be used from python code with virtually the same interface as the commandline.  

.. note::

    FlashKit understands where you are running the commands from (i.e., your current working directory). This brings us to
    the introduction of configuration files. FlashKit is intended to work with a directory tree of simulation files where
    the structure of directories has meaning as shown in the example below. This being the case, FlashKit will use the
    available configuration files in the current working directory and all those directories above to infer the intended
    options for the FlashKit command of interest. Specifically, you can either enter options for the FlashKit command at
    the commandline or in any of the configuration files in the path. We will get back to the details of how to most
    effectively use configuration files shortly.

A FlashKit command looks like the following:

.. command-output:: flashkit create xdmf --auto
    :cwd: ../../../../jobs/flashkit/driven/ug

You may see a different output if there are no FLASH simulation output files in your current working directory.

This command will create an xdmf file for use in plotting FLASH simulation output using Paraview (or other visualization 
software which understands xdmf + hdf5 files). The auto flag tells FlashKit to attempt determining what simulations files you want 
to use in creating the xdmf file. Specifically, it will look for all FLASH simulation plot files which conform to the standard 
naming convention. Many options and flags can be provided for each FlashKit command. These options and flags change the behavior of
the underling FlashKit operations provided in the library. You can see what options are available by running the FlashKit command
with the help flag or usually by providing no options to the FlashKit command.

To see the options available for the xdmf command, use the following:

.. command-output:: flashkit create xdmf --help

--------------------

The power of creation
---------------------

FlashKit provides a number of useful operations for a FLASH user, which fall into several catagories.
These are accessed in a very natural way by specifying the catagory and operations desired. 
A this time, the inteded scope of the FlashKit library looks like the following, 
where the clouds indicate functions that are not complete.

|

.. image:: /_static/Commands.png
    :alt: FlashKit Commands

|

The available FlashKit categories and overall usage of FlashKit can be provided using the following:

.. command-output:: flashkit --help

The FlashKit library provides help information at all levels.
This is useful as it can be quite difficult to remember all of the available options and 
flags for each FlashKit operation. It is convienent to be able to ask FlashKit for help 
before having to consult the FlashKit documentation.

Let's test this out, the available ``create`` operations can be provided using the following:

.. command-output:: flashkit create --help

That was helpful.

As we saw, the create catagory of operations helps us create useful files for interacting with FLASH simulations. 
For example, the ``grid`` operation creates an initial simulation grid file that is needed when running FLASH simulations
which use a stretched regular grid. We already saw the ``xdmf`` operation and how it creates the necessary file to view 
our FLASH simulation output using Paraview.

Let's take a closer look at the ``grid`` operation and its options and flags:

.. command-output:: flashkit create grid --help

That is a lot of available options and flags for changing the behavior of the ``create grid`` operation.
Let's test some of this out. For example, let's try creating a grid with 2x4 blocks with 8x12 points each in the x and y directions.
Additionally let's stretch the grid using a centered tanh method in the y direction. This is accomplished with:

.. command-output:: flashkit create grid -X 8 -Y 12 -i 2 -j 4 -b tanh_mid -RF

Notice that this time we used the short form of the options and the options and flags.

We will go into more details of the ``create`` catagory of operations in later tutorials. 

--------------------

What's in a configuration
-------------------------

The idea of configuration files, very similar to how FLASH implements a hierarchy of source units to provide inheritance,
is to provide useful context to the library behavior based on where the command is exexuted from. Specifically, configuration
files implement a depth first merge of options specified in these files; where config file options overwrite library defaults
and commandline (or python interface) provided options overwrite config file options.

Consider the following directory structure typical of a FLASH researcher, and files within.

|

.. image:: /_static/DirectoryTree.png
    :alt: Directory Tree

|

Using this directory structure as an example, if a flashkit command is run from the ``jobs/rayleigh/ra08/low/`` directory, the
order of precidence (in decending order) for options will be:

#. command line options
#. jobs/rayleigh/ra08/low/flash.toml
#. jobs/rayleigh/ra08/flash.toml
#. jobs/rayleigh/flash.toml
#. library defaults

Configuration file options are specified in the toml file under the following structure:

.. code-block::

    [category.operation]
    option = value

Now let's use this hierarchy in a simple example to see how this might be useful with ``flashkit create grid``.

At the highest level, ``jobs/rayleigh/``, let's say all simulations will use the same stretching method and domain:

.. program-output:: cat flash.toml
    :cwd: ../../../../jobs/flashkit/rayleigh

At the the next level, ``jobs/rayleigh/ra08``, let's say all simulations will use the same number and size blocks:

.. program-output:: cat flash.toml
    :cwd: ../../../../jobs/flashkit/rayleigh/ra08


At the lowest level, ``jobs/rayleigh/ra08/low``, let's say the specific simulation will use lower resolution:

.. program-output:: cat flash.toml
    :cwd: ../../../../jobs/flashkit/rayleigh/ra08/low

These options will be combined, according to the precidence ordering above, allowing us to forego the options at the prompt.
Let's see this in action.

.. command-output:: flashkit create grid -RF
    :cwd: ../../../../jobs/flashkit/rayleigh/ra08/low

This is exactly as expected.

One final note on configuration file options. Several operations, and indeed operations across categories, may share some
options. Therefore, it is benificial to have a method to specify the common options such as grid and processor information.
For example, the highest level options, ``jobs/rayleigh/``, could have been specified as:

.. program-output:: cat common.toml
    :cwd: ../../../../jobs/flashkit/rayleigh

In this case, the general option is used if the operation specific option is not provided in the configuration file. This
leads to the more complete order of precidence (in decending order) for options being:

#. command line options
#. jobs/rayleigh/ra08/low/flash.toml (operation specific)
#. jobs/rayleigh/ra08/low/flash.toml (common options)
#. jobs/rayleigh/ra08/flash.toml     (operation specific)
#. jobs/rayleigh/ra08/flash.toml     (common options)
#. jobs/rayleigh/flash.toml          (operation specific)
#. jobs/rayleigh/flash.toml          (common options)
#. library defaults

The full specification for :ref:`options<Configuration Options>` providable in configuration files can be found :ref:`here<Configuration Files>`.

--------------------
