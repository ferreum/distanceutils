"""Provides base classes."""


from operator import itemgetter, attrgetter, methodcaller
import numbers
import collections

from .bytes import BytesModel, Section, Magic, SKIP_BYTES, S_FLOAT3, S_FLOAT4
from .printing import format_transform
from .lazy import UNSET, LazyMappedSequence
from .classes import CollectorGroup, DefaultClasses
from ._common import classproperty


Classes = CollectorGroup()

TRANSFORM_MIN_SIZE = 12


class TransformError(ValueError):
    """Conflict when applying a transform."""


class NoDefaultTransformError(TypeError):
    """The default transform of the object is unknown."""


class FragmentKeyError(KeyError):

    """A fragment for a tag is not present or not implemented for its version.

    Note that importing this class is in most cases unnecessry as it extends
    `KeyError`, which is commonly caught to handle a missing entry.

    """

    def __init__(self, tag, version=None):
        if version is None:
            self.args = tag,
        else:
            self.args = tag, version
        self.tag = tag
        self.version = version

    def __str__(self):
        version = self.version
        if version is None:
            return repr(self.tag)
        else:
            return f"{self.tag!r} not implemented for version {version}"

    @property
    def is_present(self):
        "True if the fragment is present but not implemented."
        return self.version is not None


def _isclose(a, b):
    return -0.00001 < a - b < 0.00001


def _seq_isclose(sa, sb):
    for a, b in zip(sa, sb):
        if not _isclose(a, b):
            return False
    return True


class Transform(tuple):

    """Position, rotation and scale (immutable).

    Attributes & Indices & Parameters
    ---------------------------------
    pos : 3-tuple or ()
        The position as xyz coordinates.
    rot : 4-tuple or ()
        The rotation as xyzw-quaternion.
    scale : 3-tuple or ()
        The x, y and z scale.

    Elements can be an empty tuple ``()``, meaning an object-dependent default
    is being used. A transform in which all values are present is called an
    *effective* transform.

    There is also the *empty* transform ``Transform()``, used for objects which
    contain no transform value.

    """

    __slots__ = ()

    @classmethod
    def fill(cls, pos=(0, 0, 0), rot=(0, 0, 0, 1), scale=(1, 1, 1)):
        """Create a new transform, completing missing with identity values."""
        if len(pos) != 3:
            raise TypeError("Invalid pos")
        if len(rot) != 4:
            raise TypeError("Invalid rot")
        if isinstance(scale, numbers.Real):
            scale = (scale, scale, scale)
        elif len(scale) != 3:
            raise TypeError("Invalid scale")
        return cls(pos, rot, scale)

    def __new__(cls, *args):
        if len(args) not in (0, 3):
            raise TypeError('Invalid number of arguments')
        return tuple.__new__(cls, map(tuple, args))

    pos = property(itemgetter(0), doc="Position of the transform (read-only)")
    rot = property(itemgetter(1), doc="Rotation of the transform (read-only)")
    scale = property(itemgetter(2), doc="Scale of the transform (read-only)")

    @property
    def qrot(self):
        """The rotation as `numpy.quaternion` (read-only)."""
        import numpy as np, quaternion
        quaternion # dontwarn

        rot = self.rot
        return np.quaternion(rot[3], *rot[:3])

    def effective(self, pos=(0, 0, 0), rot=(0, 0, 0, 1), scale=(1, 1, 1)):
        """Create an *effective* copy given the specified default values."""
        tpos, trot, tscale = self or ((), (), ())
        return type(self)(tpos or pos, trot or rot, tscale or scale)

    @property
    def is_effective(self):
        """Check whether this transform is *effective*."""
        if not self:
            return False
        pos, rot, scale = self
        return len(pos) == 3 and len(rot) == 4 and len(scale) == 3

    def set(self, pos=None, rot=None, scale=None):
        """Create a copy with the given elements replaced."""
        opos, orot, oscale = self or ((), (), ())
        if pos is not None:
            opos = pos
        if rot is not None:
            orot = rot
        if scale is not None:
            oscale = scale
        return type(self)(opos, orot, oscale)

    def apply(self, pos=(0, 0, 0), rot=(0, 0, 0, 1), scale=(1, 1, 1)):

        """Apply the given transformation in this reference frame.

        This can be thought of as the operation used by a `Group` to calculate
        where its children end up on the level's global frame of reference.

        Only works with *effective* transforms.

        Raises
        ------
        TransformError
            If the given rotation is incompatible with the reference scale.
        TypeError
            If this or the given transform is not *effective*.

        """

        if not self.is_effective or not Transform(pos, rot, scale).is_effective:
            raise TypeError('need effective transform')

        import numpy as np, quaternion
        from .transform import rotpoint
        quaternion

        mpos, mrot, mscale = self

        qmrot = np.quaternion(mrot[3], *mrot[:3])
        qrot = np.quaternion(rot[3], *rot[:3])

        ascale = np.array(scale)
        amscale = np.array(mscale)

        rotmat = quaternion.as_rotation_matrix(qrot)
        scaleaxes = [None, None, None]
        for i, row in enumerate(rotmat):
            for j, v in enumerate(row):
                if _isclose(1, abs(v)):
                    scaleaxes[i] = j
                elif not _isclose(0, v):
                    si, sj = mscale[i], mscale[j]
                    if not _isclose(si, sj):
                        raise TransformError('Incompatible rotation and scale')
                    scaleaxes[i] = j

        rpos = tuple(mpos + rotpoint(qmrot, pos * amscale))
        qrrot = qmrot * qrot
        rrot = (*qrrot.imag, qrrot.real)

        rot_amscale = tuple(amscale[i] for i in scaleaxes)
        rscale = tuple(rot_amscale * ascale)

        return type(self)(rpos, rrot, rscale)

    def strip(self, pos=None, rot=None, scale=None):
        """Create a copy with the given values stripped if close enough."""
        import numpy as np, quaternion
        quaternion

        mpos, mrot, mscale = self or ((), (), ())

        if mpos and pos and _seq_isclose(mpos, pos):
            mpos = ()
        if mrot and rot:
            qmrot = np.quaternion(mrot[3], *mrot[:3])
            qmrot /= np.quaternion(rot[3], *rot[:3])
            if _isclose(qmrot.angle(), 0):
                mrot = ()
        if mscale and scale and _seq_isclose(mscale, scale):
            mscale = ()

        return type(self)(mpos, mrot, mscale)

    @classmethod
    def read_from(cls, dbytes):
        """Read a new transform from dbytes."""
        data = dbytes.read_bytes(12)
        if data.startswith(SKIP_BYTES):
            pos = ()
            data = data[4:]
        else:
            pos = S_FLOAT3.unpack(data)
            data = dbytes.read_bytes(8)
        # len(data) == 8
        if data.startswith(SKIP_BYTES):
            rot = ()
            data = data[4:]
        else:
            ndata = dbytes.read_bytes(12)
            rot = S_FLOAT4.unpack(data + ndata[:8])
            data = ndata[8:]
        # len(data) == 4
        if data == SKIP_BYTES:
            scale = ()
        else:
            data = data + dbytes.read_bytes(8)
            scale = S_FLOAT3.unpack(data)
        return cls(pos, rot, scale)

    def write_to(self, dbytes):
        """Write this transform to dbytes."""
        pos, rot, scale = self or ((), (), ())
        if pos:
            dbytes.write_bytes(S_FLOAT3.pack(*pos))
        else:
            dbytes.write_bytes(SKIP_BYTES)
        if rot:
            dbytes.write_bytes(S_FLOAT4.pack(*rot))
        else:
            dbytes.write_bytes(SKIP_BYTES)
        if scale:
            dbytes.write_bytes(S_FLOAT3.pack(*scale))
        else:
            dbytes.write_bytes(SKIP_BYTES)


class Fragment(BytesModel):

    """Represents a container section and its content.

    Attributes
    ----------
    dbytes : DstBytes
        The source this fragment has been read from.
    container : Section
        The container section of this fragment.
    classes : ClassesRegistry
        The registry used for contained objects and tags. Default is the
        ``DefaultRegistry``.

    """

    __slots__ = ('_raw_data', 'container', 'dbytes', 'classes')

    default_container = None

    @classproperty
    def base_container(cls):

        """The base container of this class.

        Defaults to None, or the base section of `default_container` if set.

        """

        con = cls.default_container
        if con is None:
            return None
        if con.has_version():
            return Section(con, version=None)
        return con

    @classproperty
    def container_versions(cls):

        """The container versions supported by this class.

        Defaults to None, or the version of `default_container` if it has a
        version.

        """

        con = cls.default_container
        if con is None or not con.has_version():
            return None
        return con.version

    @classmethod
    def get_default_container(cls):

        """Get the default container when creating this class.

        Returns
        -------
        container : Section
            `default_container` if it is not None.

            If `default_container` is None, returns `base_container`, with the
            highest version in `container_versions` if the section has a
            version and both are not None. If it has no version, it is returned
            as-is. Otherwise, returns None.

        """

        defcon = cls.default_container
        if defcon is not None:
            return defcon
        base = cls.base_container
        if base is None:
            return None
        if not base.has_version():
            return base
        versions = cls.container_versions
        if versions is None:
            return None
        if isinstance(versions, numbers.Integral):
            version = versions
        else:
            version = max(versions)
        return Section(base, version=version)

    is_interesting = False

    @classproperty
    def class_tag(cls):

        """Tag of this class.

        Default is the class name with "Fragment" suffix removed, and raises
        AttributeError if the name does not end with "Fragment".

        """

        name = cls.__name__
        if not name.endswith('Fragment') or name == 'Fragment':
            raise AttributeError(f"Could not get class tag for {cls!r}")
        return name[:-8]

    def __init__(self, dbytes=None, **kw):
        self.classes = kw.pop('classes', DefaultClasses)
        super().__init__(dbytes=dbytes, **kw)

    def _init_defaults(self):
        super()._init_defaults()
        con = self.get_default_container()
        if con is not None:
            self.container = con

    def _read(self, dbytes, *, container=None, classes=None, child_prober=None):

        """Read data of the Fragment.

        Parameters
        ----------
        container : Section
            Container Section of this Fragment. `dbytes` needs to be positioned
            at `content_start` of the section if set. If omitted, it is read
            from `dbytes` before reading its content.
        classes : ClassesRegistry
            If not None, it is first assigned to the `classes` attribute of the
            object.
        child_prober : str
            Specifies the child object prober name for ObjectFragment. Only
            accepted here to allow passing it without checking for this
            object's type.

        """

        self.dbytes = dbytes
        if classes is not None:
            self.classes = classes
        if container is None:
            container = Section(dbytes, seek_end=False)
        self.container = container
        self.end_pos = container.end_pos
        self._read_section_data(dbytes, container)

    def visit_write(self, dbytes):
        con = getattr(self, 'container', None)
        sec = self._get_write_section(con)
        with dbytes.write_section(sec):
            yield self._visit_write_section_data(dbytes, sec)

    def _get_write_section(self, sec):
        return sec or self.get_default_container()

    @property
    def raw_data(self):

        """The unmodified raw bytes of this fragment.

        Only valid for fragments that have been read or if this property has
        been assigned first.

        This attribute is initialized lazily. File errors may occur on access.

        Returns
        -------
        data : bytes
            The bytes of this fragment.

        Raises
        ------
        AttributeError
            If this fragment has no assigned raw data and has no source and
            container information to initialize it.

        """

        try:
            return self._raw_data
        except AttributeError:
            pass
        try:
            dbytes = self.dbytes
            sec = self.container
            start = sec.content_start
            size = sec.content_size
        except AttributeError:
            raise AttributeError(f"Missing source and/or container information")
        with dbytes:
            dbytes.seek(start)
            data = dbytes.read_bytes(size)
            self._raw_data = data
        return data

    @raw_data.setter
    def raw_data(self, value):
        self._raw_data = value

    def clone(self):

        """Clones the fragment.

        Subclasses should override `_clone_data` to copy values to the new
        instance. The default just copies `raw_data`.

        The container is always copied, but only its type information is
        retained.

        """

        new = type(self)()
        try:
            con = self.container
        except AttributeError:
            pass
        else:
            new.container = Section(con)
        self._clone_data(new)
        return new

    def _clone_data(self, new):
        new.raw_data = self.raw_data

    def _read_section_data(self, dbytes, sec):
        """Read data of the given section."""

    def _visit_write_section_data(self, dbytes, sec):

        """Write data of the given section (trampolined).

        Default implementation delegates to `_write_section_data`.

        """

        self._write_section_data(dbytes, sec)
        return
        yield

    def _write_section_data(self, dbytes, sec):

        """Non-trampolined version of `_write_section_data`.

        The default implementation just writes this object's `raw_data`.

        """

        dbytes.write_bytes(self.raw_data)

    def __str__(self):
        from io import StringIO
        sio = StringIO()
        flags = ('allprops', 'sections', 'transform', 'offset',
                 'objects', 'subobjects', 'groups', 'fragments')
        self.print(file=sio, flags=flags)
        return sio.getvalue()

    def _print_type(self, p):
        hint = ''
        try:
            tag = self.class_tag
        except AttributeError:
            tag = None
        if tag is None:
            type_str = 'Unknown'
        else:
            type_str = repr(tag)

        actual_str = ''
        ver_str = ''
        overridden = False
        try:
            container = self.container
        except AttributeError:
            pass
        else:
            try:
                con_tag = self.classes.fragments.get_tag(container)
            except KeyError:
                con_tag = None
            if con_tag != tag:
                overridden = tag is not None
                if con_tag is None:
                    actual_str = " (container Unknown)"
                else:
                    actual_str = f" (container {con_tag!r})"

            if not overridden and tag is not None and container.has_version():
                version = self.container.version
                ver_str = f" version {version!r}"

        if overridden:
            hint = ' [overridden]'
        elif tag is None:
            hint = ' [dummy]'
        else:
            hint = ''

        p(f"Fragment: {type_str}{actual_str}{ver_str}{hint}")

    def _visit_print_data(self, p):
        if 'sections' in p.flags:
            try:
                container = self.container
            except AttributeError:
                pass
            else:
                p(f"Container:")
                with p.tree_children(1):
                    yield container.visit_print(p)


@Classes.fragments.fragment
class ObjectFragment(Fragment):

    """Common fragment providing the basics of any object.

    Attributes
    ----------
    real_transform : Transform
        The transform of the object.
    children : list of BaseObject
        The children of the object.
    has_children : bool
        Whether the object has a list of children. If True, a list of children
        is written even if it is empty.

    """

    __slots__ = ('real_transform', 'has_children', 'children',
                 '_child_prober')

    base_container = Section.base(Magic[3], 1)
    container_versions = 0

    def _init_defaults(self):
        super()._init_defaults()
        self.real_transform = Transform()
        self.has_children = False
        self.children = ()

    def _read(self, dbytes, *args, **kw):
        self._child_prober = getattr(self.classes, kw['child_prober'])
        Fragment._read(self, dbytes, *args, **kw)

    def _read_section_data(self, dbytes, sec):
        has_children = False
        children = ()
        if sec.content_size >= TRANSFORM_MIN_SIZE:
            transform = Transform.read_from(dbytes)
            if dbytes.tell() + Section.MIN_SIZE < sec.end_pos:
                s5 = Section(dbytes, seek_end=False)
                has_children = True
                children = self._child_prober.lazy_n_maybe(
                    dbytes, s5.count, start_pos=s5.content_start)
        else:
            transform = Transform()
        self.real_transform = transform
        self.has_children = has_children
        self.children = children

    def _visit_write_section_data(self, dbytes, sec):
        transform = self.real_transform
        children = self.children
        has_children = self.has_children or children
        if transform or has_children:
            transform.write_to(dbytes)
        if has_children:
            with dbytes.write_section(Magic[5]):
                for obj in children:
                    yield obj.visit_write(dbytes)

    def clone(self):
        """ObjectFragments cannot be cloned."""
        raise NotImplementedError("Cannot clone object")


def _object_property(name, default=None, doc=None):
    if doc is None:
        doc = f"property forwarded to 'ObjectFragment'"

    # Optimized access to the very frequently used ObjectFragment.
    obj_key = ObjectFragment.base_container.to_key(noversion=True)
    def get_object_fragment(self):
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == obj_key:
                return self.fragments[i]
            i += 1
        return None

    def fget(self):
        frag = get_object_fragment(self)
        return getattr(frag, name, default)
    def fset(self, value):
        frag = get_object_fragment(self)
        setattr(frag, name, value)
    return property(fget, fset, None, doc=doc)


class default_fragments(object):

    """Decorator for specifying default fragments of a BaseObject.

    New instances of annotated classes are initialized with specified
    fragments.

    Parameters
    ----------
    classes : any number of fragment classes
        The fragment classes of which to add the container sections to the
        decorated class.

    """

    @classmethod
    def add_to(cls, target, *classes):

        """Add sections of given classes.

        Parameters
        ----------
        target : BaseObject class
            The class to specify default fragments for.
        classes : any number of fragment classes
            The fragment classes of which to add the container sections.

        """

        if not all(callable(c) for c in classes):
            raise TypeError("Not all args are callable")
        containers = (con for con in map(methodcaller('get_default_container'), classes)
                      if con is not None)
        cls.add_sections_to(target, *containers)

    @staticmethod
    def add_sections_to(target, *sections):

        """Add given fragment sections.

        Parameters
        ----------
        target : BaseObject class
            The class to specify default fragments for.
        sections : any number of fragment sections
            The fragment sections to add.

        """

        try:
            registered = target.__sections
        except AttributeError:
            registered = []
        target.__sections = registered + [s for s in sections
                                          if s not in registered]

    @staticmethod
    def get_sections(target):

        """Get default fragment sections of the given class.

        Parameters
        ----------
        target : BaseObject class
            The class of which to get the default fragment sections.

        Returns
        -------
        sections : list of Section
            The default fragment sections of `target`.

        Raises
        ------
        AttributeError
            If default fragments for `target` were never specified.

        """

        return target.__sections

    def __init__(self, *classes):
        self.classes = classes

    def __call__(self, target):
        self.add_to(target, *self.classes)
        return target


class _MappedSequenceView(collections.Sequence):

    __slots__ = ('_source', '_func')

    def __init__(self, source, func):
        self._source = source
        self._func = func

    def __len__(self):
        return len(self._source)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return list(map(self._func, self._source[index]))
        else:
            return self._func(self._source[index])

    def __iter__(self):
        return map(self._func, self._source)


def _FragmentsContainerView(frags):
    return _MappedSequenceView(frags, attrgetter('container'))


@default_fragments(ObjectFragment)
class BaseObject(Fragment):

    """Represents data within a ``Magic[6]`` Section.

    Contains a list of fragments exposed by the `fragments` property.

    Fragments can also be accessed by tag using the subscript notation::

        frag = obj['Animator']
        obj['Animator'] = anim_frag
        del obj['Animator']
        has_anim = 'Animator' in frag

    These also verify that accessed fragments are implemented and support the
    present version. The methods `get_any` and `has_any` don't perform this
    check.

    Practically all instances of this class contain an `ObjectFragment` that
    provides the `children`, and `real_transform` properties.

    Attributes
    ----------
    has_children : bool
        Whether this object has a list of children. If True, a list of children
        is written even if empty.

    Class Attributes
    ----------------
    child_class_name : str
        Name of the prober to use to find the classes of `children`.
    is_object_group : bool
        True if this is a Group object, False otherwise.
    has_children : bool
        Default value for the `has_children` instance attribute. Set to True to
        force writing of the list of children even if empty.
    default_transform : Transform
        The default transform of this class. Required to use the `transform`
        property.

    """

    type = None
    child_classes_name = 'base_objects'
    is_object_group = False
    has_children = False

    default_transform = None

    @classproperty
    def class_tag(cls):

        """The tag of this class.

        Defaults to the `type` attribute specified by the class.

        """

        return cls.type

    def __init__(self, *args, **kw):
        container = kw.get('container')
        if container is not None:
            self.type = container.type
        super().__init__(*args, **kw)

    def clone(self):
        """BaseObjects cannot be cloned."""
        raise NotImplementedError("Cannot clone object")

    real_transform = _object_property(
        'real_transform', default=Transform(),
        doc="The transform as read from the file.")

    children = _object_property(
        'children', default=(),
        doc="The list of contained children.")

    @property
    def transform(self):
        """The *effective* transform.

        Like `real_transform`, but always returns an *effective* transform.

        The `default_transform` value needs to be set to the object-specific
        default transform for this to work.

        Raises
        ------
        NoDefaultTransformError
            If this class doesn't specify its default transform with the
            `default_transform` attribute.

        """
        t = self.real_transform
        defs = self.default_transform
        if defs is None:
            raise NoDefaultTransformError(
                f"default transform unknown for {self.type!r}")
        return t.effective(*defs)

    @transform.setter
    def transform(self, value):
        if not isinstance(value, Transform):
            value = Transform(*value)
        if value:
            default = self.default_transform
            if default:
                value = value.strip(*default)
        self.real_transform = value

    fragments = property(attrgetter('_fragments'),
                         doc="The list of contained fragments.")

    @fragments.setter
    def fragments(self, value):
        self._sections = _FragmentsContainerView(value)
        self._fragments = value

    sections = property(attrgetter('_sections'),
                        doc=("Containers of the fragments of this object."
                             " (read-only view of fragments*.container)"))

    def fragment_by_type(self, typ):

        """Get fragment by class.

        Not recommended. Use ``self[tag]`` instead.

        """

        probe = self.classes.fragments.probe_section
        i = 0
        for sec in self.sections:
            sec_typ = probe(sec)
            if issubclass(sec_typ, typ):
                return self.fragments[i]
            i += 1
        return None

    def filter_fragments(self, section_pred):

        """Iterate fragments filtered by section.

        This is useful to reduce work when iterating fragments, as unselected
        fragments aren't instantiated.

        Parameters
        ----------
        section_pred : function (Section) -> bool
            The predicate function. Returns True if the fragment should be
            yielded, False otherwise.

        Yields
        ------
        fragment : Fragment
            Fragments of the sections for which `section_pred` returned True.

        """

        fragments = self.fragments
        i = 0
        for sec in self.sections:
            if section_pred(sec):
                yield fragments[i]
            i += 1

    def __getitem__(self, tag):

        """Get a fragment by tag, if implemented.

        Provides ``self[tag] -> Fragment``.

        Parameters
        ----------
        tag : str
            The tag of the fragment to get.

        Returns
        -------
        fragment : Fragment
            The fragment with the given tag.

        Raises
        ------
        FragmentKeyError
            If fragment is not present or not implemented. Use the exception's
            `is_present` attribute to check for the reason. Importing
            `FragmentKeyError` is in most cases unnecessary, as it extends
            `KeyError`.
        TagError
            If the given tag is not registered.

        """

        base_key, versions = self.classes.fragments._get_tag_impl_info(tag)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                break
            i += 1
        else:
            raise FragmentKeyError(tag)

        fragments = self.fragments

        # We always allow getting the fragment if it has the same tag,
        # regardless of whether we have a registered implementation.
        # This allows retrieving it after assignment via __setitem__.
        peeked = LazyMappedSequence.peek(fragments, i)
        if peeked is not UNSET:
            if getattr(peeked, 'class_tag', None) != tag:
                raise FragmentKeyError(tag, sec.version)
            return peeked

        if (versions != 'all' and sec.has_version()
                and sec.version not in versions):
            raise FragmentKeyError(tag, sec.version)

        return fragments[i]

    def __setitem__(self, tag, frag):

        """Add or replace a fragment by tag.

        Provides ``self[tag] = frag``.

        Verifies that the tag and fragment's container match.

        Parameters
        ----------
        tag : str
            The tag of the fragment.
        frag : Fragment
            The fragment.

        Raises
        ------
        KeyError
            If the tag doesn't match the fragment's container.
        TagError
            If the given tag is not registered.

        """

        base_key = self.classes.fragments.get_base_key(tag)
        if frag.container.to_key(noversion=True) != base_key:
            raise KeyError(f"Invalid fragment container: expected"
                           f" {base_key!r} but got {frag.container!r}")
        ftag = frag.class_tag
        if ftag != tag:
            raise KeyError(f"Invalid fragment tag: fragment tag is {ftag!r}"
                           f" but expected {tag!r}")
        frags = list(self.fragments)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                frags[i] = frag
                break
            i += 1
        else:
            frags.append(frag)
        self.fragments = frags

    def __delitem__(self, tag):

        """Remove a fragment by tag.

        Provides ``del self[tag]``.

        Parameters
        ----------
        tag : str
            The tag of the container of fragment to remove.

        Raises
        ------
        KeyError
            If there is no fragment with the given tag.
        TagError
            If the given tag is not registered.

        """

        base_key = self.classes.fragments.get_base_key(tag)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                frags = list(self.fragments)
                del frags[i]
                self.fragments = frags
                break
            i += 1
        else:
            raise KeyError(f"Fragment with tag {tag!r} is not present")

    def __contains__(self, tag):

        """Check whether a fragment with given tag is present and implemented.

        Provides ``tag in self``.

        Parameters
        ----------
        tag : str
            The tag to check.

        Returns
        -------
        implemented : bool
            Whether a fragment with given tag is present and implemented.

        Raises
        ------
        TagError
            If the given tag is not registered.

        """

        base_key, versions = self.classes.fragments._get_tag_impl_info(tag)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                break
            i += 1
        else:
            return False

        # Peek operation analogous to __getitem__.
        peeked = LazyMappedSequence.peek(self.fragments, i)
        if peeked is not UNSET:
            return peeked.class_tag == tag

        return (versions == 'all' or not sec.has_version()
                or sec.version in versions)

    def __iter__(self):
        "Not iterable. Implemented only to prevent __getitem__ iteration."
        raise TypeError(f"{type(self).__name__!r} object is not iterable")

    def get_any(self, tag):

        """Get fragment with given tag, regardless of implementation.

        Parameters
        ----------
        tag : str
            The tag of the fragment to get.

        Returns
        -------
        fragment : Fragment or None
            The fragment with the given tag, or None if there is no fragment
            with the given tag.

        Raises
        ------
        TagError
            If the given tag is not registered.

        """

        base_key = self.classes.fragments.get_base_key(tag)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                return self.fragments[i]
            i += 1
        return None

    def has_any(self, tag):

        """Check whether a fragment with given tag is present.

        Parameters
        ----------
        tag : str
            The tag of the fragment.

        Returns
        -------
        present : bool
            Whether there is any fragment with the given tag.

        Raises
        ------
        TagError
            If the given tag is not registered.

        """

        base_key = self.classes.fragments.get_base_key(tag)
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                return True
        return False

    def _read_section_data(self, dbytes, sec):
        self.type = sec.type
        self._sections = Section.lazy_n_maybe(dbytes, sec.count)
        self._fragments = LazyMappedSequence(
            self._sections, self._read_fragment)

    def _read_fragment(self, sec):
        if sec.exception:
            # failed to read section - return object containing the error
            return Fragment(exception=sec.exception)
        dbytes = self.dbytes
        dbytes.seek(sec.content_start)
        classes = self.classes
        return classes.fragments.maybe(
            dbytes, probe_section=sec,
            child_prober=self.child_classes_name,
            classes=classes)

    def _get_write_section(self, sec):
        try:
            cid = sec.id
        except AttributeError:
            cid = None
        return Section(Magic[6], self.type, id=cid)

    def _visit_write_section_data(self, dbytes, sec):
        for frag in self.fragments:
            yield frag.visit_write(dbytes)

    def _init_defaults(self):
        super()._init_defaults()
        sections = [sec for sec in default_fragments.get_sections(self)
                    if sec is not None]
        fragments = []
        for sec in sections:
            cls = self.classes.fragments.probe_section(sec)
            frag = cls(container=sec)
            if cls is ObjectFragment:
                frag.has_children = self.has_children
            fragments.append(frag)
        self.fragments = fragments

    def _repr_detail(self):
        supstr = super()._repr_detail()
        return f" type={self.type!r}{supstr}"

    def _print_type(self, p):
        p(f"Object type: {self.type!r}")

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.real_transform)}")
        if 'fragments' in p.flags and self.fragments:
            if 'allprops' in p.flags:
                p(f"Fragments: {len(self.fragments)}")
                with p.tree_children(len(self.fragments)):
                    for frag in self.fragments:
                        p.tree_next_child()
                        yield frag.visit_print(p)
            else:
                pred = self.classes.fragments.is_section_interesting
                frags = self.filter_fragments(pred)
                try:
                    frag = next(frags)
                except StopIteration:
                    pass
                else:
                    p(f"Fragments: {len(self.fragments)} <filtered>")
                    with p.tree_children():
                        p.tree_next_child()
                        yield frag.visit_print(p)
                        for frag in frags:
                            p.tree_next_child()
                            yield frag.visit_print(p)

    def _visit_print_children(self, p):
        num = len(self.children)
        if num:
            p(f"Children: {num}")
            with p.tree_children(num):
                for obj in self.children:
                    p.tree_next_child()
                    yield obj.visit_print(p)


def require_type(*args, func=None):

    """Decorator to add a type check for reading.

    Annotated classes raise an exception when trying to read from a source that
    contains an object with a different type.

    Parameters
    ----------
    type : str (optional)
        The expected type of objects. If omitted, the `type` attribute of the
        decorated class is used.
    func : function (str) -> bool
        If specified, call the given function to validate the type. The
        function returns True if the type is valid, False otherwise.

    """

    def check(sec):
        if callable(typ):
            if not typ(sec.type):
                raise ValueError(f"Invalid object type: {sec.type!r}")
        else:
            if sec.type != typ:
                raise ValueError(f"Invalid object type: {sec.type!r}"
                                 f" (expected {typ})")
    def decorate(cls):
        superfunc = cls._read_section_data
        def checking_read_data(self, dbytes, sec):
            check(sec)
            superfunc(self, dbytes, sec)
        cls._read_section_data = checking_read_data
        return cls

    if func is not None:
        if args:
            raise ValueError
        typ = func
        return decorate
    elif len(args) != 1:
        raise ValueError
    elif callable(args[0]):
        typ = args[0].type
        return decorate(args[0])
    else:
        typ = args[0]
        return decorate


# vim:set sw=4 ts=8 sts=4 et:
