create xdmf
===========

|

The page defines the application programing interface specification for the ``xdmf`` operation.

--------------------

|

The command line interface for the ``xdmf`` catagory of operations is:

.. program-output:: flashkit create xdmf --help

Please consult the discussion on :ref:`command line syntax<Command Line Syntax>` for 
help in formating the above options (e.g., LIST or PATH).

--------------------

|

The python interface for the ``xdmf`` operation is accessed with the following code:

.. code-block::

    from flashkit import flash
    ...
    flash.create.xdmf(options=value, flag=True, ...)

The python interface specification for ``xdmf`` is as follows:

.. autofunction:: flashkit.api.create._xdmf::xdmf

--------------------

|

The complete specification of library defaults values (as shown above) and mappings is as follows:

.. program-output:: flashkit create xdmf --option

Please consult the tutorial discussion on :ref:`configuration file formating<Configuration Files>` for 
help in specifying the above options in a `flash.toml` file and what mapping general options are, as well 
as the full specification on FlashKit library :ref:`options<Configuration Options>`.

--------------------
