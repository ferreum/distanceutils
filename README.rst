*************
distanceutils
*************

Utilities for the Refract Studios game Distance.
################################################

Intalling
=========

All modules and utilities are provided by the package `distanceutils`.
For example, using pip::

  $ pip install --user distanceutils


Scripts
=======

The following executable scripts are provided:


dst-bytes
---------

Prints various contents of .bytes files.

See `.bytes Support`_ for a list of supported files.

Output can be modified by passing flags to the `-f` option:

* transform - Prints transform (position, rotation, scale) of level objects

* offset - Prints hexadecimal offset of objects in the .bytes file

* nosubobjects - Don't print subobjects

* nogroups - Don't print objects inside groups

* description - Print level descriptions in WorkshopLevelInfos

* nosort - Don't sort LocalLeaderboard entries (entries are not sorted by time
  in the file)

* sections - Prints the sections that each object consists of (object format
  intrinsic)

* unknown - Prints unknown data for each object


dst-objtobytes
--------------

Takes a wavefront .obj file and generates a .bytes CustomObject made from
simples.

* The resulting object is a Group containing WedgeGS objects.

* Subgroups are generated if the .obj contains groups.

* Supports material colors if matching .mtl file is found.

* Generates between one and two WedgeGS for each triangle (two are needed for
  non-right triangles).

* Loading large objects (> 1000 triangles) considerably slows down level load
  times.


dst-teletodot
-------------

Takes a level .bytes file and generates a Graphviz dot document of teleporter
connections.

For example, the connections can be viewed using xdot:

::

  $ dst-teletodot my_level.bytes | xdot -


WorkshopLevelInfos database
---------------------------

For easier querying of levels, as a first step, a SQLite cache database is
generated from WorkshopLevelInfos.bytes, followed by querying this database.


dst-mklevelinfos
''''''''''''''''

Generates the cache database from WorkshopLevelInfos.bytes. See --help for
options.


dst-querymaps
'''''''''''''

Queries the cache database. See --help for options.


_`.bytes Support`
=================

Reading of the following .bytes files and objects is implemented:


* Level (`<userdir>/Levels/\*\*.bytes`)

  * LevelSettings

  * Layers

  * Objects in layers

  * Subobjects of objects

  * Some Object and Subobject properties, see `Level Objects`_

* CustomObjects (`<userdir>/CustomObjects/<name>.bytes`)

  * These work exactly the same as objects found on levels. See `Level Objects`_

* LocalLeaderboard (`<userdir>/LocalLeaderboards/<level>/<mode_id>.bytes`)

  - Version 0..1

  * Leaderboard entries

    * Player name

    * Time

    * Replay ID

* Replay (`<userdir>/LocalLeaderboards/<level>/<mode_id>_<replay_id>.bytes`)

  - Version 0..4

  * Player name

  * Steam profile ID (version 1..4)

  * Finish time (version 0 and 2..4)

  * Replay duration (version 2..4)

  * Car name

  * Car colors

* LevelInfos (`<userdir>/Settings/LevelInfos.bytes`)

  * Level Entries

    * Level name

    * Level unique identifier (path in `<userdir>/Levels/`)

    * Level file base name

    * Enabled modes

    * Medal times and scores

* WorkshopLevelInfos (`<userdir>/Levels/WorkshopLevels/WorkshopLevelInfos.bytes`)

  * Workshop level entries

    * Steam workshop entry ID

    * Workshop title

    * Workshop description

    * Update and published date

    * Workshop tags

    * Author steam user ID

    * Author steam user name

    * Level unique identifier (path below `<Userdir>/Levels/`, always starts with `WorkshopLevels/`)

    * Published by this steam user

    * Number of upvotes and downvotes

    * Rating by this steam user (None/Positive/Negative)

* ProfileProgress (`<userdir>/Profiles/Progress/<name>.bytes`)

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

Writing is only supported for Group and WedgeGS:

* Group

  * Grouped objects

  * Group name

* WedgeGS

  * type (can be set to generate any GS with compatible properties: `SphereGS`
    generates a sphere)

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
