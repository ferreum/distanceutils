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

For this script, the additional modules ``numpy`` and ``numpy-quaternion`` need
to be installed.

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

Remove selected objects from a level file.

Takes an input and an output filename. The option ``-t`` matches object types
by regex. ``-n <num>`` selects matching objects by index, ``-a`` selects all
matching objects.

For example, to remove all roads from "my_level.bytes"::

  $ dst-filterlevel my_level.bytes result.bytes -t Road -a


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


.. vim:set sw=2 ts=2 sts=0 et sr ft=rst fdm=manual tw=0:
