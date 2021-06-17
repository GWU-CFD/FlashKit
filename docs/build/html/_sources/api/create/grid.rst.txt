create grid
===========

|

The page defines the application programing interface specification for the ``grid`` operation.

--------------------

|

The command line interface for the ``grid`` catagory of operations is:

.. program-output:: flashkit create grid --help

Please consult the discussion on :ref:`command line syntax<Command Line Syntax>` for 
help in specifying the format of the above options (e.g., LIST or DICT).

--------------------

|

The python interface for the ``grid`` operation is accessed with the following code:

.. code-block::

    from flashkit import flash
    ...
    flash.create.grid(<keyword arguments>)

The python interface specification for ``grid`` is as follows:

.. autofunction:: flashkit.api.create._grid::grid

--------------------

|

The complete specification of library defaults values (as shown above) and mappings is as follows:

.. program-output:: flashkit create grid --option

Please consult the tutorial discussion on :ref:`configuration file formating<Configuration Files>` for 
help in specifying the above options in a `flash.toml` file and what mapping general options are, as well 
as the full specification on FlashKit library :ref:`options<Configuration Options>`.

--------------------
