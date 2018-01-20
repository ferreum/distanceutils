Changelog
---------

* version 0.4.5

  * Added compatibility for new LevelInfos entry version.

  * ``vis`` filter now visualizes objects regardless of fragment version
    where possible.

  * Bugfixes

    * Fixed reading level settings that contain the author's name.

    * Fixed WorldText not read/written correctly.

    * Perserve non-empty MaterialFragment that has no entries correctly.

* version 0.4.4

  * Added compatibility for level settings of Distance build 5795 up to at
    least 5814.

* version 0.4.3

  * ``vis`` filter now modifies golden simples according to whether their
    collision is enabled.

  * ``vis`` now shows colliders of ``AbilityCheckpointOLD`` and
    ``EmpireMovingPillar``.

  * ``vis`` can now apply to multiple components of the same type for the same
    level object (which doesn't yet exist in game).

  * ``rm`` filter now applies to ``:all`` by default, added ``:print`` for
    listing matches and aborting instead.

  * ``goldify`` can now replace all old simples (with ``unsafe`` category).

  * ``goldify`` filter can now handle simples with omitted colors (which
    happened in old versions with default colors).

  * Internal changes

    * Made ``BaseObject.sections`` a read-only view of its fragments'
      containers.

    * Fixed some caching issues with ``fragment_by_type()``.

    * Filter's ``add_args`` argparser now uses ``:`` as prefix instead of
      ``--``.

* version 0.4.2

  * Allow assigning any sequence to transform attribute again (fixes
    ``dst-objtobytes``).

* version 0.4.1

  * Added ``invert`` option to ``rm`` filter.

  * ``vis`` filter now replicates cooldown ring rotation with animators. (not
    needed for checkpoints, because checkpoint hitboxes are static)

  * Improved ``vis`` filter error handling.

  * Fixed animations copied from scaled objects.

  * Object transform values that are equal to the object's default are now
    omitted on assignment.

* version 0.4.0

  * Added ``rm`` filter for removing matching objects.

  * Added ``goldify`` filter for replacing most old simples with golden
    simples.

  * Added ``unkill`` filter for replacing kill grids with harmless simples.

  * Added ``vis`` filter for visualizing various things.

  * Added ``settings`` filter for modifying level settings.

  * ``dst-filterlevel`` now utilizes these filters. Its old parameters have
    been removed. The same functionality is now available with the ``rm``
    filter.

  * ``write()`` methods now also accept a file name or a file object.

  * New ``GoldenSimple`` object used for all non-spline golden simples.

  * New ``OldSimple`` object.

  * Added proper ``Transform`` class.

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

