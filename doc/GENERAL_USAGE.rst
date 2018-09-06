*************
General Usage
*************

Glossary
--------

Probing
'''''''

Probing means inspecting the data of a file to find a suitable class that can
be used to read it.

A prober's ``probe`` method can be used to find a suitable class for the
current file position, while the ``read`` and ``maybe`` methods immediately
read the object.

Category
''''''''

Classes are grouped into different categories, each fulfilling a different
purpose. Useful categories are listed below.

Categories offer different methods to interact with available classes. These
include probing, creating new instances or retrieving a class by tag. See
``help(distance.classes.ClassCollection)`` for details.

Tag
'''

Classes of a category can be referenced by a string tag that carries a
different meaning depending on the category. For level objects it is the type
string of the object, for fragments it is the component name as found in the
level editor.

Composite Prober
''''''''''''''''

Some categories are composite probers. They work with the classes of other
categories and can only be used for probing. Accessing classes by tag and other
query methods are not supported by such a category.

Categories
----------

The following categories of the ``DefaultClasses`` object may be useful in
scripts. They are available as attributes:

>>> from distance import DefaultClasses
>>> # use the 'file' category...
>>> obj = DefaultClasses.file.read('tests/in/leaderboard/version_1.bytes')
>>> assert obj.entries[0].time == 57400

``file``
''''''''

Composite prober that contains classes of all top-level objects of .bytes
files. This can be used to read any .bytes file that is written by the game.

The ``distance.PROBER`` is a reference to this category.

``level_objects``
'''''''''''''''''

Contains all classes of primary objects that can be found in levels and
CustomObjects.

Tags in this category are the same as the type string of the object. For
example, ``DefaultClasses.level_objects.create('CubeGS')`` returns a new
``GoldenSimple`` object with the ``type`` set to ``CubeGS``.

For unknown tags, the ``LevelObject`` class is used, which provides only basic
methods. Note that the game accepts such an empty instance in most cases and
sets all properties to their default values.

*Note: This category shouldn't be used directly to read .bytes files. For
reading CustomObjects files, the* ``customobjects`` *category should be used.*

``level_subobjects``
''''''''''''''''''''

Some level objects have subobjects which contain more information about the
object. Some are unnoticeable game intrinsics, others are visible in the
properties pane in the editor.

These can be accessed via the ``children`` attribute of any regular (anything
but ``Group`` objects) level object.

One notable class is the ``Teleporter`` object, which can be found as a child
of any teleporter object and contains all teleporter-specific information. Note
that this subobject class is distinct from the primary ``Teleporter`` object
even though it has the same type string.

For unknown tags, the ``SubObject`` class is used, which is a subclass of
``LevelObject``.

``fragments``
'''''''''''''

Contains the components of any level object, subobject or even the non-level
objects. Objects contain almost no data on their own. Instead, they are
composed of fragments which carry all data of the object.

Tags of these classes specify the type of the fragment except their version,
i.e. Fragments of the same type that implement different versions use the same
tag. The tags are otherwise chosen freely because they are not part of .bytes
files. As a convention, the corresponding name seen in the level editor is
used.

For example, ``DefaultClasses.fragments.create('Animator')`` returns a new
``AnimatorFragment`` with the highest implemented version.

There is no fallback for unknown tags. Fragments that are not implemented can
usually be omitted from objects. The game then uses default values in their
place.

``non_level_objects``
'''''''''''''''''''''

Contains any other file format classes that are not levels. This includes
replays, LocalLeaderboards, ProfileProgress, WorkshopLevelInfos and LevelInfos.

Trying to probe a level or CustomObject with this category results in a
``ProbeError``.

``level_like``
''''''''''''''

Composite prober that contains the ``level`` and ``level_objects`` categories.
This should be used to support both level files and CustomObjects files.

As non-level objects have the same structure as CustomObjects, objects of the
``non_level_objects`` category are explicitly excluded from this category,
resulting in ``ProbeError``.

``customobjects``
'''''''''''''''''

Composite prober that contains all classes of the ``level_objects`` category
and explicitly excludes all objects of the ``non_level_objects`` category such
that probing non-CustomObjects files results in a ``ProbeError``.

This should be used to support just CustomObjects files.

``common``
''''''''''

This category is not used for probing, but as a way to provide commonly-used
classes that don't fit in any category on their own. This includes shared level
object classes that can be used for different types such as ``GoldenSimple``
and ``OldSimple``, and the ``Replay`` class, which has the quirk that its type
string contains the player's name and needs to be special-cased.

Listing
-------

Provided classes and categories can be listed by executing the ``distance``
module in a terminal, specifying what to list.

List the names of all categories::

   python -m distance --list-categories

List all classes of all categories::

   python -m distance --list-classes

List all classes of a single category::

   python -m distance --list-classes level_objects

List a single class of the ``fragments`` category by tag::

   python -m distance --list-fragment Animator

Single Classes
--------------

The ``distance`` module also directly provides the following classes, all of
which can be found in categories above. These are useful to access just the
corresponding kind of file. Trying to read a file of the wrong type results in
an error:

=======================  ========
Class                    Location
``Leaderboard``          ``LocalLeaderboards/**/<mode_id>.bytes``
``Level``                ``Levels/**.bytes``
``LevelInfos``           ``Settings/LevelInfos.bytes``
``ProfilePrgress``       ``Profiles/Progress/<name>.bytes``
``Replay``               ``LocalLeaderboards/**/<mode_id>_<replay_id>.bytes``
``WorkshopLevelInfos``   ``Levels/WorkshopLevels/WorkshopLevelInfos.bytes``
=======================  ========

Reading Objects
---------------

Passing a file name as ``str`` or ``bytes`` to a provided class's constructor
or ``maybe`` classmethod or to a prober's ``read`` or ``maybe`` method opens
the file with the given name and reads the object from it.

Opening a file by name like this reads the whole file into memory first. If
this is undesired, open the file manually:

>>> from distance import Level
>>> with open("tests/in/level/test-straightroad.bytes", 'rb') as f:
...     level = Level(f)
...     level.layers[0].objects[0].type
'LevelEditorCarSpawner'

Content of files is read on-demand as it is accessed. This means that the file
needs to be kept open for as long as the object is used. This also means that
the file needs to be seekable. This lazy-loading changes the seek position of
the file.

As the file is read in very small pieces, this direct I/O may be noticeably
slower if a lot of objects are accessed, because reading and seeking the real
file is less efficient than an in-memory buffer. Performance may be better when
accessing little amounts of data, such as only reading a level's name.

Writing Objects
---------------

Object's and fragment's properties can be modified and written back to a file.

For example, changing a level's name:

>>> from distance import Level
>>> level = Level("my_level.bytes")
>>> level.settings.name = 'My Changed Level'
>>> level.write("my_changed_level.bytes")

The argument of the ``write`` method can be any ``str`` or ``bytes`` object
specifying the file name to write, or an already opened file in binary mode.

Note that any object and fragment has a ``write`` method that can be used to
write only that object to a file. This can be used to create CustomObject
files.

Incomplete Classes
''''''''''''''''''

Some fragments contain fields that are not implemented yet. Data of these
fields is only copied from the original object. These fields are usually named
``unk_#`` or ``rem`` ("remainder").

Such objects cannot simply be created with their constructor. Creating such an
object would require assigning ``bytes`` to these fields that have the correct
length and contain data that the game accepts.

Object IDs
''''''''''

.bytes files contain a lot of IDs that need to be consistent within a file. If
a file contains multiple objects with the same ID, the file cannot be loaded
properly (with varying effects).

This means that extracting objects from one file works fine, but duplicating
objects or merging objects from different files may lead to errors when the
game loads the file.

NamedPropertiesFragment
'''''''''''''''''''''''

This fragment and its subclasses have a common key-value format.

They are mainly found on old objects in the game, some of which are still used
in the latest versions.

They use absolute offets within the file, which need to be updated when they
are relocated. For this reason, these fragments always need to be known by the
fragment prober. If a fragment of this format is not registered as
NamedPropertiesFragment and gets relocated, loading the file will lead to
errors.

This should be no problem for regular usage, as these fragments are known by
the default ``fragments`` category.

Example Usages
--------------

Create a new level object:

>>> from distance import DefaultClasses
>>> obj = DefaultClasses.level_objects.create('CubeGS', emit_index=23)
>>> assert obj.type == 'CubeGS'
>>> assert obj.emit_index == 23

Referencing and creating fragments by tag:

>>> obj = DefaultClasses.level_objects.create('CubeGS')
>>> anim = DefaultClasses.fragments.create('Animator')
>>> obj['Animator'] = anim
>>> obj['Animator'].motion_mode = 4
>>> del obj['Animator']
>>> assert 'Animator' not in obj

