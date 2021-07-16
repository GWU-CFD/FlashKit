build simulation
================

|

The page defines the application programing interface specification for the ``simulation`` operation.

--------------------

|

The command line interface for the ``simulation`` catagory of operations is:

.. program-output:: flashkit build simulation --help

Please consult the discussion on :ref:`command line syntax<Command Line Syntax>` for 
help in formating the above options (e.g., LIST or DICT).

--------------------

|

The python interface for the ``simulation`` operation is accessed with the following code:

.. code-block::

    from flashkit import flash
    ...
    flash.build.simulation(options=value, flags=True, ...)

The python interface specification for ``simulation`` is as follows:

.. autofunction:: flashkit.api.build._simulation::simulation

--------------------

|

The complete specification of library defaults values (as shown above) and mappings is as follows:

.. program-output:: flashkit build simulation --option

Please consult the tutorial discussion on :ref:`configuration file formating<Configuration Files>` for 
help in specifying the above options in a `flash.toml` file and what mapping general options are, as well 
as the full specification on FlashKit library :ref:`options<Configuration Options>`.

--------------------
