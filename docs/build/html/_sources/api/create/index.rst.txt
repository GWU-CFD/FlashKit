flashkit create
===============

|

The page defines the application programing interface specification for the ``create`` category.

--------------------

|

The command line interface for the ``create`` catagory of operations is:

.. program-output:: flashkit create --help

--------------------

|

The python interface for the ``create`` catagory of operations is accessed with the following code:

.. code-block::

    from flashkit import flash
    ...
    flash.create.operation(options=value, flag=True, ...)

--------------------

|

The interface specification each of the operations within the ``create`` catagory of operations can be found in the following:

.. toctree::

    block
    grid
    interp
    par
    xdmf

--------------------
