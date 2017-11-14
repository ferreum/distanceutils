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
the right object or the ``PROBER``:

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

The following executable scripts are provided:


dst-bytes
---------

Dump various data from .bytes files.

See `Object support`_ for a list of supported files.

Output can be modified by passing flags (comma-separated, or multiple options)
to the ``-f`` option:

* transform - Print transform (position, rotation, scale) of level objects

* offset - Print hexadecimal offset of objects in the .bytes file

* nosubobjects - Don't print subobjects

* nogroups - Don't print objects inside groups

* nofragments - Don't print any fragments (hides most object details)

* allprops - Print all fragment properties

* description - Print level descriptions in WorkshopLevelInfos

* nosort - Don't sort LocalLeaderboard entries (entries are not sorted by time
  in the file)

* sections - Print the sections that each object consists of (object format
  intrinsic)

* track - Print connection reference IDs of track elements

Example::

  $ dst-bytes -f transform my_level.bytes

Prints all objects in "my_level.bytes" including their position.


dst-mkcustomobject
------------------

Extract a CustomObject from a level or from another CustomObject.

Example::

  $ dst-mkcustomobject Levels/MyLevels/my_level.bytes CustomObjects/my_obj.bytes -n 0 -t Zone

The above extracts the first object of which the type name contains ``Zone``.

If multiple objects match and ``-n`` is not used, a numbered list of candidates
is printed.


dst-objtobytes
--------------

Take a wavefront .obj file and generate a .bytes CustomObject made from
simples.

* The resulting object is a Group containing WedgeGS objects.

* Subgroups are generated if the .obj contains groups.

* Uses material colors if matching .mtl file is found.

* Generates between one and two WedgeGS for each triangle (two are needed for
  non-right triangles).

* Loading large objects (> 1000 triangles) considerably slows down level load
  times.

Example::

  $ dst-objtobytes teapot.obj teapot.bytes


dst-filterlevel
---------------

Apply filters to a level or CustomObject.

For a list of filters, see filters_.

Takes an input and an output filename. Any amount of filters can be specified,
which are applied in the given order.

Filters are specified by name, and can take optional arguments.

Examples::

  # use filter 'rm' with arguments 'type=Road' and 'all'
  rm:type=Road:all

  # use filter 'goldify' without arguments
  goldify

Filters provide a ``help`` argument, which just prints the filter's help, and
aborts the program without executing any filters.

*Note: due to an implementation detail, the help lists arguments with a* ``--``
*prefix that needs to be ignored for now.*


.. _filters: ./doc/FILTERS.rst


dst-teletodot
-------------

Take a level .bytes file and generate a Graphviz dot document of teleporter
connections.

For example, the connections can be viewed using xdot::

  $ dst-teletodot my_level.bytes | xdot -


WorkshopLevelInfos database
---------------------------

For easier querying of levels, as a first step, a SQLite cache database is
generated from WorkshopLevelInfos.bytes, followed by querying this database.


dst-mklevelinfos
''''''''''''''''

Generate the cache database from WorkshopLevelInfos.bytes. See --help for
options.


dst-querymaps
'''''''''''''

Query the cache database. See --help for options.


