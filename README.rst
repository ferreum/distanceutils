*************
distanceutils
*************

Read and modify .bytes files of the Refract Studios game Distance.
##################################################################

Installing
==========

All modules and utilities are provided by the package ``distanceutils``.
For example, using pip::

  $ pip install --user numpy
  $ pip install --user distanceutils

Due to a problem with another dependency (``numpy-quaternion``), ``numpy``
needs to be installed first with a separate command.

_`Basic Usage`
==============

The core of this project can be imported with the ``distance`` module. With
this module, .bytes files written by the game can be read, modified and written
back to a file.

Reading a file is as easy as importing the module and passing a file name to
the right class or a prober. Files can be written back to a file with
modifications:

>>> from distance import Level
>>> level = Level("my_level.bytes")
>>> level.settings.name
'My Level'
>>> level.layers[0].objects[-1].type
'EmpireEndZone'
>>> level.settings.name = 'My changed level'
>>> level.write("my_changed_level.bytes")

For an advanced introduction, see `General Usage`_.

For more example usages, see the scripts provided with the distance_scripts_
module.

For a complete list of provided classes, run the following shell command::

   python -m distance --list-classes

For objects that are missing here, base classes are used, so these objects can
be written back to a file without changes.


.. _`doc string`: ./distance/__init__.py
.. _`General Usage`: ./doc/GENERAL_USAGE.rst
.. _distance_scripts: ./distance_scripts/


Scripts
=======

The following executable scripts are included with this package:

`dst-bytes`_ - Print various data of given .bytes files.

`dst-mkcustomobject`_ - Extract a CustomObject from a level or from another CustomObject.

`dst-filterlevel`_ - Apply filters to a level or CustomObject. For a list of filters, see filters_.

`dst-objtobytes`_ - Generate a CustomObject from a wavefront .obj 3D model file.

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

