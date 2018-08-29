*************
General Usage
*************

Glossary
--------

Probing
'''''''

Probing means inspecting the data of a file to find an implementing class that
can be used to read it.

A prober's ``probe`` method can be used to find a suitable class for the
current file position, while the ``read`` and ``maybe`` methods immediately
read the object.

Category
''''''''

Classes are grouped into different categories, each fulfilling a different
purpose. Useful categories are listed below.

Categories offer different methods to interact with available classes. These
include probing, creating a new instance or retrieving a class by tag. See
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

Composite prober that contains all top-level objects of .bytes files. This can
be used to read any .bytes file that is written by the game.

The ``distance.PROBER`` object is a reference to this category.

``level_objects``
'''''''''''''''''

Contains any classes of primary objects that can be found in levels.

Tags in this category are the same as the type string of the object. For
example, ``DefaultClasses.level_objects.create('CubeGS')`` returns a new
``GoldenSimple`` object with the ``type`` set to ``CubeGS``.

If there is no implementation of the specified type, the ``LevelObject`` class
is used, which provides only basic methods. Note that the game accepts such an
empty instance in most cases, which sets all properties to their default
values.

*Note: This category shouldn't be used directly to read .bytes files. For
reading CustomObjects files, the* ``customobjects`` *category should be used.*

``level_subobjects``
''''''''''''''''''''

Some level objects have subobjects which in turn contain more information about
the object. Some are unnoticeable game intrinsics, some are visible in the
properties pane in the editor.

These can be accessed via the ``children`` attribute of any regular (anything
but ``Group`` objects) level object.

One notable class is the ``Teleporter`` object, which can be found as a child
of any teleporter object and contains all teleporter-specific information. Note
that this subobject class is distinct from the primary ``Teleporter`` object
even though it has the same type string.

``fragments``
'''''''''''''

Contains the components of any level object, subobject or even the non-level
objects. Objects contain almost no data on their own. Instead, they are
composed of fragments which carry all data of the object.

Tags of these classes specify the type of the fragment minus their version,
i.e. Fragments of the same type that implement different versions use the same
tag. The tags are otherwise chosen freely because they are not part of .bytes
files. As a convention, the corresponding name seen in the level editor is
used.

For example, ``DefaultClasses.fragments.create('Animator')`` returns a new
``AnimatorFragment`` with the highest implemented version.

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
that probing non-level files results in a ``ProbeError``.

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

Provided classes can be listed by executing the ``distance`` module in a
terminal, specifying what to list.

List the names of all categories::

   python -m distance --list-categories

List all classes of all categories::

   python -m distance --list-classes

List all classes of a single category::

   python -m distance --list-classes level_objects

List a single class of the ``fragments`` category by tag::

   python -m distance --list-fragment Animator

Writing Objects
---------------

Object's and fragment's properties can be modified and written back to a file.

For example, a level's name can be changed:

>>> from distance import Level
>>> level = Level("my_level.bytes")
>>> level.settings.name = 'My Changed Level'
>>> level.write("my_changed_level.bytes")

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

