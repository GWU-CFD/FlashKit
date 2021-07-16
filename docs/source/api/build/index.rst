flashkit build
==============

|

The page defines the application programing interface specification for the ``build`` category.

--------------------

|

The command line interface for the ``build`` catagory of operations is:

.. program-output:: flashkit build --help

--------------------

|

The python interface for the ``build`` catagory of operations is accessed with the following code:

.. code-block::

    from flashkit import flash
    ...
    flash.build.operation(options=value, flag=True, ...)

--------------------

|

The interface specification each of the operations within the ``build`` catagory of operations can be found in the following:

.. toctree::

    jobs
    port
    scaling
    simulation

--------------------
