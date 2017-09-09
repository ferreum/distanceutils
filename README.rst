*************
distanceutils
*************

Utilities for the game Distance by Refract Studios.
###################################################

Intalling
=========

All modules and utilities are in the package "distanceutils".
For example, to install them using pip:

::

  $ pip install --user distanceutils


.bytes Support
==============

Reading of the following .bytes files and objects is implemented:


* Level (<profiledir>/Levels/\*\*.bytes)

  * LevelSettings

  * Layers

  * Objects in layers

  * Subobjects of objects

  * See "Level Object support"

* CustomObjects (<profiledir>/CustomObjects/<name>.bytes)

  * These work exactly the same as objects found on levels. See "Level Object support"

* LocalLeaderboard (<profiledir>/LocalLeaderboards/<level>/<mode_id>.bytes)

  - Version 0..1

  * Leaderboard entries

    * Player name

    * Time

    * Replay ID

* Replay (<profiledir>/LocalLeaderboards/<level>/<mode_id>_<replay_id>.bytes)

  - Version 0..4

  * Player name

  * Steam profile ID (version 1..4)

  * Finish time (version 0 & 2..4)

  * Replay duration (version 2..4)

  * Car name

  * Car colors


Level Object Support
--------------------

* LevelSettings

  - Version 0..9

  * Level name

  * Medal times and scores

  * Enabled game modes

  * Enabled/disabled abilities

  * Difficulty

* Layers

  * Flags (Active, Frozen, Visible)

  * Object list


Various Objects
'''''''''''''''

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

  * Text 0..4


Subobjects
''''''''''

* Teleporter (Found on anything with teleporter properties like actual
  Teleporter, TeleporterVirus, VirusSpiritSpawner, etc and even EmpireStart/EndZone)

  * Link ID

  * Destination ("Teleports to")

  * Trigger checkpoint (true/false)




Scripts
=======

The following scripts are included in the package.


dst-bytes
---------

Takes a .bytes file and prints various information found in the file.

See section ".bytes support" for a list of supported files.


dst-objtobytes
--------------

Takes a wavefront .obj file and generates a .bytes CustomObject made from
simples.


dst-teletodot
-------------

Takes a level .bytes file and generates a Graphviz dot document of teleporter connections.

For example, the connections can be viewed using xdot:

::

  $ dst-teletodot my_level.bytes | xdot -


WorkshopLevelInfos database
---------------------------

For easier querying of levels, as a first step, a sqlite cache database is
generated from WorkshopLevelInfos.bytes followed by querying the database.


dst-mklevelinfos
''''''''''''''''

Generates the cache database from WorkshopLevelInfos.bytes.


dst-querymaps
'''''''''''''

Queries the cache database.


.. vim:set sw=2 ts=2 sts=0 et sr ft=rst fdm=manual tw=0:
