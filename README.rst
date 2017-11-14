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


filter: ``rm``
''''''''''''''

Remove objects with matching type, index or sections.

For example, to remove all roads from "my_level.bytes"::

  $ dst-filterlevel my_level.bytes result.bytes -o rm:type=Road:all


filter: ``goldify``
'''''''''''''''''''

Replace old simples (``[Emissive]<shape>[WithCollision]``) with golden simples.

Opaque simples are replaced with equal-looking golden simples. Emissive simples
on the other hand look different, because the texture of old simples is not
available for golden simples.

Not all simples have exact golden counterparts. The quality of the replacement
differs depending on the shape and other properties of the simple. For this
reason the replacements are put into categories:

* ``safe`` (default); all exact replacements:
  ``Cube``, ``Hexagon``, ``Octahedron``.

  These shapes are exact matches with their golden counterparts, and are
  scaled to exactly match the original.

* ``inexact``; scale, rotation or position may not be exact:
  ``Pyramid``, ``Dodecahedron``, ``Icosahedron``, ``Ring``, ``RingHalf``,
  ``TearDrop``, ``Tube``, ``IrregularCapsule001``, ``IrregularCapsule002``
  and all ``safe`` replacements.

  The transformations of these objects were estimated by binary-search. The
  lower precision may be noticeable for objects with very large scale, but
  generally, this category should be safe to use.

  ``Dodecahedron`` and ``Icosahedron`` need to be rotated in a way that they
  cannot retain independent scale on y and z axes. The filter skips the
  replacement if this is the case, retaining the old object.

* ``unsafe``; objects that don't have the correct shape:
  ``Sphere``, ``Cone``, ``Cylinder``, ``Wedge``, ``TrueCone``, ``Plane``,
  ``Capsule``, ``FlatDrop``, ``CylinderTapered`` and all ``inexact``
  replacements.

  The shape differences may be noticeable depending on the scale:

  The rounded surfaces of ``Sphere``, ``Cone``, ``TrueCone`` and ``Cylinder``
  are made of a different number of triangles.

  The old ``Wedge`` is not exactly right-angled, but the new ``WedgeGS`` is.

  ``[Emissive]PlaneWithCollision`` can be passed through in one direction, but
  has collision in the other. The replacement ``PlaneGS`` has collision in both
  directions.

  ``CapsuleGS`` has different proportions and different number of triangles.

  ``FlatDrop`` is replaced with ``CheeseGS``, which is not even close to the
  correct shape, but it's the best fit available.

  ``CylinderTapered`` is replaced with ``CircleFrustumGS``, which has a
  different angle and number of triangles.

* ``bugs``; just fix collisions with ``Cube`` objects.

  This is a work-around for the glitch with collisions with  old ``Cube``
  simples. This category just replaces all ``[Emissive]CubeWithCollision``
  with ``CubeGS``.

The category is specified as argument to the filter. For example, to use all
replacements::

  $ dst-filterlevel my_level.bytes result.bytes -o goldify:unsafe


filter: ``unkill``
''''''''''''''''''

Replace kill grids with harmless (kind-of similar looking) simples. Useful for
exploration, practice, and finding hidden routes.

Note: only finite kill grids are replaced for now, because they are most
significant for routing, and infinite ones are more difficult to replace.

Example::

  $ dst-filterlevel my_level.bytes result.bytes -o unkill

Collisions are enabled by default. To disable collisions specify
``unkill:nocollision``.

Color of the grid is copied to the simple by default. To use the default grid
color specify ``unkill:nocolor``.


filter: ``vis``
'''''''''''''''

Visualize various things by adding simples in their position.

Example::

  $ dst-filterlevel my_level.bytes result.bytes -o vis

Colliders of different objects are color-coded to indicate their effect.

Teleporter colliders have additional indicators for their connection status:

* Green: Bidirectional (destination teleporter leads back to this one)

* Blue: Unidirectional, but at least one different teleporter leads to this
  teleporter.

* Yellow: Unidirectional (can enter, but nothing leads to this teleporter)

* Pink: This teleporter leads nowhere, but at least one teleporter leads here.

* Red: not connected, or leads to itself


filter: ``settings``
''''''''''''''''''''

Modify level settings.

For example, to enable all modes and append "(filtered)" to the name::

  $ dst-filterlevel my_level.bytes result.bytes -o settings:modes=all:namefmt='{} (filtered)'


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


_`Module usage`
===============

The functionality of this project can be imported using the ``distance`` module.
The module's `doc string`_ has a short introduction for reading files.

For example usages, see the scripts provided by this package, in the
distance_scripts_ module.

For a complete list, see the modules levelobjects_ and levelfragments_.


Writing
-------

Any object can be written as-is back into a new file. There is limited support
for modifications of object's attributes. This includes removing children,
moving (translating) level objects, removing level objects, changing object's
types, and adding newly generated objects.

For a complete list, see the modules levelobjects_ and levelfragments_.

For a (now incomplete) list of supported objects, see `Object support`_.

.. _`doc string`: ./distance/__init__.py
.. _`Object support`: ./doc/OBJECT_SUPPORT.rst
.. _levelobjects: ./distance/levelobjects.py
.. _levelfragments: ./distance/levelfragments.py
.. _distance_scripts: ./distance_scripts/

