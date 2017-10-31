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

See `.bytes Support`_ for a list of supported files.

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
  ``Sphere``, ``Cone``, ``Cylinder``, ``Wedge``, ``TrueCone``, ``Plane`` and
  all ``inexact`` replacements.

  The shape differences may be noticeable depending on the scale:

  The rounded surfaces of ``Sphere``, ``Cone``, ``TrueCone`` and ``Cylinder``
  are made of a different number of triangles.

  The old ``Wedge`` is not exactly right-angled, but the new ``WedgeGS`` is.

  ``[Emissive]PlaneWithCollision`` can be passed through in one direction, but
  has collision in the other. The replacement ``PlaneGS`` has collision in both
  directions.

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


_`.bytes Support`
=================

Reading of the following .bytes files and objects is implemented:


* Level (``<userdir>/Levels/**.bytes``)

  * LevelSettings

  * Layers

  * Objects in layers

  * Subobjects of objects

  * Some Object and Subobject properties, see `Level Objects`_

* CustomObjects (``<userdir>/CustomObjects/<name>.bytes``)

  * These work exactly the same as objects found on levels. See `Level Objects`_

* LocalLeaderboard (``<userdir>/LocalLeaderboards/<level>/<mode_id>.bytes``)

  - Version 0..1

  * Leaderboard entries

    * Player name

    * Time

    * Replay ID

* Replay (``<userdir>/LocalLeaderboards/<level>/<mode_id>_<replay_id>.bytes``)

  - Version 0..4

  * Player name

  * Steam profile ID (version 1..4)

  * Finish time (version 0 and 2..4)

  * Replay duration (version 2..4)

  * Car name

  * Car colors

* LevelInfos (``<userdir>/Settings/LevelInfos.bytes``)

  * Level Entries

    * Level name

    * Level unique identifier (path in ``<userdir>/Levels/``)

    * Level file base name

    * Enabled modes

    * Medal times and scores

* WorkshopLevelInfos (``<userdir>/Levels/WorkshopLevels/WorkshopLevelInfos.bytes``)

  * Workshop level entries

    * Steam workshop entry ID

    * Workshop title

    * Workshop description

    * Update and published date

    * Workshop tags

    * Author steam user ID

    * Author steam user name

    * Level unique identifier (path within ``<Userdir>/Levels/``, always starts with ``WorkshopLevels/``)

    * Published by this steam user

    * Number of upvotes and downvotes

    * Rating by this steam user (None/Positive/Negative)

* ProfileProgress (``<userdir>/Profiles/Progress/<name>.bytes``)

  * Level progress entries

    * Level unique identifier

    * Completion for each mode (unplayed/started/finished/medal)

    * Time/Score for each mode

  * List of unlocked official levels

  * List of found stunt tricks

  * List of unlocked adventure stages

  * Most user statistics displayed in garage menu

  * Found Trackmogrify modifiers


_`Level Objects`
----------------

* LevelSettings

  - Version 0..9

  * Level name

  * Medal times and scores

  * Enabled game modes

  * Enabled/disabled abilities (version 1..9)

  * Difficulty (version 2..9)

  * Music ID

  * Skybox name (version 0..3)

* Layers

  * Flags (Active, Frozen, Visible)

  * Layer name

  * Object list


Various Level Objects
'''''''''''''''''''''

* Any object

  * Object type

  * transform (position, rotation, scale)

  * Subobjects (game intrinsics, not necessarily visible in level editor)

* Group

  * Grouped objects

  * Custom name

* WorldText

  * Text

* InfoDisplayBox

  * Text #0..4

* CarScreenTextDecodeTrigger

  * Text and time text

  * Other miscellaneous trigger properties

* GravityTrigger

  * Disable gravity

  * Drag scale

  * Angular drag scale

  * Music ID

  * One time trigger

  * Reset before trigger

  * Disable music trigger

* ForceZoneBox

  * Custom name

  * Force direction

  * Global force

  * Force type

  * Gravity magnitude

  * Disable global gravity

  * Wind speed

  * Drag multiplier

* EnableAbilitiesBox

  * Enabled abilities (Enable Flying, Jumping, Boosting, JetRotating)


Subobjects
''''''''''

Some level objects have subobjects which in turn contain more information about
the object. Some are unnoticeable game intrinsics, some are visible in the
properties pane in the editor.

* Any subobject

  * Subobject type

  * transform (position, rotation, scale; mostly unset)

  * Subobjects (Subobjects can have subobjects too)

* Teleporter (Found on anything with teleporter properties like actual
  Teleporter, TeleporterVirus, VirusSpiritSpawner, etc. and even EmpireStart/EndZone)

  * Link ID

  * Destination ("Teleports to")

  * Trigger checkpoint (true/false)

* WinLogic (found on EmpireEndZone/EmpireEndZoneSimple)

  * DelayBeforeBroadcast


Writing objects
---------------

Most objects read from a file can be written as-is to a different file. Some
properties reference absolute offsets within the file, which are rewritten
automatically.

Additionally .bytes files contain a lot of IDs that need to be consistent
within a file. If an ID occurs multiple times in a single file, it cannot be
loaded (with varying effects). This means that extracting objects from one file
works fine, but duplicating objects or merging objects from different files
leads to errors when loading the level.


These objects can be generated:

* Group

* GoldenSimple (any non-spline golden simple)

The following properties can be modified:

* any level object

  * transform (position, rotation, scale)

  * Subobjects

* Group

  * Grouped objects

  * Group name

* GoldenSimple

  * type (Specifies which golden simple to generate: ``SphereGS`` generates a
    sphere. Splines are not supported.)

  * Material/Emit/Reflect/Spec color

  * Texture scale

  * Texture offset

  * Image/Emit index

  * Flip texture UV

  * World mapped

  * Disable diffuse

  * Disable bump

  * Bump strength

  * Disable reflect

  * Disable collision

  * Additive transparency

  * Multiplicative transparency

  * Invert emit

