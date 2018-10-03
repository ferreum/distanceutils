Changelog
---------

* version 0.5.1 (unreleased)

  * Fixed issues with new teleporter objects.

  * Fixed level corruption with ``CarVoiceTrigger``.

  * New objects: ``SetAbilitiesTrigger``, ``WarpAnchor``.

* version 0.5.0

  * All objects can now be written back to a file including their
    modifications.

  * Added ``file`` filter for applying filter chains from files.

  * Added ``downgrade`` filter for downgrading objects to support older game
    versions. Only applies to Animators and EventListeners for now such that
    they work with build 5824, the latest drmfree version as of writing. Some
    effects may be lost in the process.

  * Passing single dash ``-`` file name to ``dst-bytes``, ``dst-filterlvel`` or
    ``dst-mkcustomobject`` now means stdin or stdout as appropriate. This
    allows chaining these commands in shell pipelines.

  * Fragments are now identified by tags.

    * Object's fragments can be accessed with the subscript syntax
      (``obj['Animator']``, ``'Animator' in obj``), which ensures an
      implementation of the fragment.

    * Object's ``get_any('Animator')`` and ``has_any('Animator')`` methods are
      counterparts that don't care about the implementation.

    * ``dst-bytes`` shows these tags when listing fragments.

  * Enum constants are not directly exposed in the ``distance`` module any
    more. They must now be imported via the ``distance.constants`` module.

  * Many methods have been cleaned up or removed as there are now better ways
    to do the same thing.

    * ``filtered_fragments`` is now called ``filter_fragments``. The
      predicate now only gets the section as argument.

    * ``BaseObject.iter_children`` and ``Level.iter_objects`` have been
      removed. Use ``BaseObject.children`` or ``Level.layers[...].objects``
      instead.

    * Probably a lot more.

  * ``DefaultClasses`` provides a centralized way to access available classes.
    See `General Usage`_ for an overview.

  * Internal changes

    * The ``construct`` module is now used to implement most fragments.

    * The ``trampoline`` module is now used to lift nesting limits when writing
      or printing objects. (Reading did not have this limitation as objects are
      read lazily.)

    * Object implementations are now loaded on-demand ("autoloading") to
      prevent worsening import time of the ``distance`` module.

      * Autoloading and class registries and probers are implemented in the
        ``distance.classes`` module. This replaces the previous "probers".

    * Provided object and fragment classes have been moved to an internal
      module. They can be accessed via the ``DefaultClasses`` registry in the
      ``distance`` module. The file format classes ``Level``, ``Replay``,
      ``Leaderboard``, ``LevelInfos``, ``ProfileProgress`` and
      ``WorkshopLevelInfos`` are still available in the ``distance`` module.
      See `General Usage`_ for an overview.

    * Made declaring creatable objects easier.

      * Fragment classes now specify supported containers with the
        ``base_container``, ``container_versions`` and ``default_container``
        attributes.

      * Object's fragment attributes are now specified using the
        ``DefaultClasses.fragments.fragment_attrs`` decorator.

      * Renamed material attribute decorator to ``material_attrs``.

      * Fragments belonging to objects are now specified with the
        ``default_fragments`` decorator. The ``fragment_attrs`` and
        ``material_attrs`` decorators also add the target fragments.

    * It is now an error to pass additional keyword arguments to constructors
      that don't also exist as class attributes. Previously these would be
      blindly set on the created object. In the future, this may be improved to
      only allow assignment of declared fields.

    * It is now an error to pass unhandled keyword arguments to ``read`` and
      related functions. Previously these would be silently ignored.

    * Exception messages now have nicer formatted position info.

* version 0.4.7

  * Linked to the correct repository in the package info.

* version 0.4.6

  * Added setters and deleters for most named property attributes.

  * Added ability properties to ability triggers.

  * Calculate medal points of ProfileProgress files.

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


.. _`General Usage`: ./doc/GENERAL_USAGE.rst

