create par
==========

|

The page defines the application programing interface specification for the ``par`` operation.

--------------------

|

The command line interface for the ``par`` catagory of operations is:

.. program-output:: flashkit create par --help

Please consult the discussion on :ref:`command line syntax<Command Line Syntax>` for 
help in formating the above options (e.g., LIST or DICT).

--------------------

|

The python interface for the ``par`` operation is accessed with the following code:

.. code-block::

    from flashkit import flash
    ...
    flash.create.par(option=value, flag=True, ...)

The python interface specification for ``par`` is as follows:

.. autofunction:: flashkit.api.create._par::par

--------------------

|

The complete specification of library defaults values (as shown above) and mappings is as follows:

.. program-output:: flashkit create par --option

Please consult the tutorial discussion on :ref:`configuration file formating<Configuration Files>` for 
help in specifying the above options in a `flash.toml` file and what mapping general options are, as well 
as the full specification on FlashKit library :ref:`options<Configuration Options>`.

--------------------

|

The complete specification of library template sources is as follows:

.. program-output:: flashkit create par --available

Please consult the tutorial discussion on :ref:`template file formating<Template Files>` for 
help in applying the above sources in a template file and what template sources are, as well 
as the full specification on FlashKit library :ref:`templates<Template Options>`.

--------------------
