*************
distanceutils
*************

Utilities for the Refract Studios game Distance.
################################################

Installing
==========

All modules and utilities are provided by the package ``distanceutils``.
For example, using pip::

  $ pip install --user distanceutils

Many operations also require the packages ``numpy`` and ``numpy-quaternion`` to
be installed.


_`Module usage`
===============

The functionality of this project can be imported with the ``distance`` module.

Reading a file is as easy as importing the module and passing a file name to
the right class or to the ``PROBER``:

.. code:: pycon

  >>> from distance import Level
  >>> level = Level("my_level.bytes")
  >>> level.settings.name
  'My Level'
  >>> level.layers[0].objects[-1].type
  'EmpireEndZone'

The module's `doc string`_ provides further introduction for reading files.

For more example usages, see the scripts provided with the distance_scripts_
module.

For a complete list of supported level objects, see the
distance.levelobjects_ and distance.levelfragments_ modules.


Writing
-------

Any object can be written as-is back into a new file. There is limited support
for modifications of object's attributes. This includes removing children,
moving (translating) level objects, removing level objects, changing object's
types, and adding newly generated objects.

For example, a level's name can be changed:

.. code:: pycon

  >>> from distance import Level
  >>> level = Level("my_level.bytes")
  >>> level.settings.name = 'My Changed Level'
  >>> level.write("my_changed_level.bytes")

For a complete list, see the objects defined in the modules
distance.levelobjects_ and distance.levelfragments_.

For a (now incomplete) list of supported objects, see `Object support`_.


.. _`doc string`: ./distance/__init__.py
.. _`Object support`: ./doc/OBJECT_SUPPORT.rst
.. _distance.levelobjects: ./distance/levelobjects.py
.. _distance.levelfragments: ./distance/levelfragments.py
.. _distance_scripts: ./distance_scripts/


Scripts
=======

The following executable scripts are included with this package:

`dst-bytes`_ - Dump various data from .bytes files.

`dst-mkcustomobject`_ - Extract a CustomObject from a level or from another CustomObject.

`dst-objtobytes`_ - Generate a CustomObject from a wavefront .obj 3D model file.

`dst-filterlevel`_ - Apply filters to a level or CustomObject. For a list of filters, see filters_.

`dst-teletodot`_ - Take a level .bytes file and generate a Graphviz dot document of teleporter connections.

`dst-mklevelinfos`_ - Generate the cache database from WorkshopLevelInfos.bytes.

`dst-querymaps`_ - Query the cache database.


.. _filters: ./doc/FILTERS.rst

.. _`dst-bytes`: ./doc/SCRIPTS.rst#dst-bytes
.. _`dst-mkcustomobject`: ./doc/SCRIPTS.rst#dst-mkcustomobject
.. _`dst-objtobytes`: ./doc/SCRIPTS.rst#dst-objtobytes
.. _`dst-filterlevel`: ./doc/SCRIPTS.rst#dst-filterlevel
.. _`dst-teletodot`: ./doc/SCRIPTS.rst#dst-teletodot
.. _`dst-mklevelinfos`: ./doc/SCRIPTS.rst#workshoplevelinfos-database
.. _`dst-querymaps`: ./doc/SCRIPTS.rst#workshoplevelinfos-database

