Changelog
---------

* version 0.4.0

  * Added ``GoldenSimple`` object used for all non-spline golden simples.

  * Added ``rm`` filter for removing matching objects.

* Added ``goldify`` filter for replacing most old simples with golden
  simples.

  * Added ``unkill`` filter for replacing kill grids with harmless simples.

  * ``dst-filterlevel`` now utilizes these filters. Its old parameters have
    been removed. The same functions are now available with the ``rm``
    filter.

  * ``write()`` methods now also accept a file name or a file object.

* version 0.3.4

  * Added a missing import to main ``distance`` module.

  * Cleaned up internals.

* version 0.3.3

  * Added imports and doc to main ``distance`` module.

  * Cleaned up code.

* version 0.3.2

  * Improved performance.

  * Added some missed named properties and added support for an older format.

* version 0.3.1

  * Fragments are now also only loaded on first access.

  * Added ``filtered_fragments`` to filter fragments by type without loading
    them.

* version 0.3.0

  * First version able to filter most (all?) levels reliably.

  * Updated existing level object implementations to handle the remaining
    named properties correctly.

  * Added ``dst-filterlevel`` script entry point for ``filterlevel``.

  * Constructors now also accept a file handle or a file name instead of a
    ``DstBytes`` object. See ``distance.bytes.DstBytes.from_arg`` for details.

* version 0.2.3

  * Implemented reading and writing of position-sensitive named properties
    which cannot be copied byte-wise. Some fragments are not implemented yet,
    so trying to load modified levels in game still leads to errors.

  * Added the ``searchfrags`` script to detect such fragments.

* version 0.2.2

  * Implemented re-writing of ``Level`` and ``Layer`` objects. Most modified
    levels fail to load because some level objects cannot be copied
    byte-wise.

  * Added the ``filterlevel`` script to try modifying levels.

* version 0.2.1

  * Fixed writing of CustomObject sections found in some old levels.

* version 0.2.0

  * Data of all level objects is now persisted and can be re-written to
    create CustomObject .bytes files. Some objects which cannot be copied
    byte-wise lose their properties when copied this way.

  * Added ``mkcustomobject`` script to try to extract CustomObjects from
    levels. Exported as ``dst-mkcustomobject``.

