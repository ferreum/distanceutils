*******
Scripts
*******

The following executable scripts are provided:


_`dst-bytes`
------------

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


.. _`Object support`: ./doc/OBJECT_SUPPORT.rst


_`dst-mkcustomobject`
---------------------

Extract a CustomObject from a level or from another CustomObject.

Example::

  $ dst-mkcustomobject Levels/MyLevels/my_level.bytes CustomObjects/my_obj.bytes -n 0 -t Zone

The above extracts the first object of which the type name contains ``Zone``.

If multiple objects match and ``-n`` is not used, a numbered list of candidates
is printed.


_`dst-objtobytes`
-----------------

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


_`dst-filterlevel`
------------------

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


.. _filters: ./doc/FILTERS.rst


_`dst-teletodot`
----------------

Take a level .bytes file and generate a Graphviz dot document of teleporter
connections.

For example, the connections can be viewed using xdot::

  $ dst-teletodot my_level.bytes | xdot -


_`WorkshopLevelInfos database`
------------------------------

For easier querying of levels, as a first step, a SQLite cache database is
generated from WorkshopLevelInfos.bytes, followed by querying this database.


_`dst-mklevelinfos`
'''''''''''''''''''

Generate the cache database from WorkshopLevelInfos.bytes. See --help for
options.


_`dst-querymaps`
''''''''''''''''

Query the cache database. See --help for options.


