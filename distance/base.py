"""Provides BaseObject."""


from operator import itemgetter, attrgetter
import numbers
import collections

from .bytes import BytesModel, Section, Magic, SKIP_BYTES, S_FLOAT3, S_FLOAT4
from .printing import format_transform
from .lazy import LazyMappedSequence
from .prober import ProberGroup
from ._default_probers import DefaultProbers


Probers = ProberGroup()

TRANSFORM_MIN_SIZE = 12


class TransformError(ValueError):
    pass


class NoDefaultTransformError(TypeError):
    pass


class FragmentKeyError(KeyError):
    "A fragment for a tag is present but not implemented for its version."

    def __init__(self, tag, version=None):
        if version is None:
            super().__init__(tag)
        else:
            super().__init__(f"{tag!r} not implemented for version {version}")
        self.version = version

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

    position, rotation and scale are represented as tuples of three, four
    and three values, respectively.

    Any of these elements can also be missing (represented as empty tuple "()")
    meaning an object-dependent default is being used. A transform in which all
    values are present is called an "effective" transform.

    There is also the "empty" transform "Transform()", used for objects which
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

        """Create a new transform.

        Arguments
        ---------
        Either no arguments (for the empty Transform) or three values
        (position, rotation, scale).

        """

        if len(args) not in (0, 3):
            raise TypeError('Invalid number of arguments')
        return tuple.__new__(cls, map(tuple, args))

    pos = property(itemgetter(0), doc="Position of the transform (read-only)")
    rot = property(itemgetter(1), doc="Rotation of the transform (read-only)")
    scale = property(itemgetter(2), doc="Scale of the transform (read-only)")

    @property
    def qrot(self):
        import numpy as np, quaternion
        quaternion # dontwarn

        rot = self.rot
        return np.quaternion(rot[3], *rot[:3])

    def effective(self, pos=(0, 0, 0), rot=(0, 0, 0, 1), scale=(1, 1, 1)):
        """Create an effective copy given the specified default values."""
        tpos, trot, tscale = self or ((), (), ())
        return type(self)(tpos or pos, trot or rot, tscale or scale)

    @property
    def is_effective(self):
        """Check whether this transform is effective."""
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

        Only works with "effective" transforms.

        Raises
        ------
        TransformError
            If the given rotation is incompatible with the reference scale.
        TypeError
            If this or the given transform is not effective.

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
        if len(pos):
            dbytes.write_bytes(S_FLOAT3.pack(*pos))
        else:
            dbytes.write_bytes(SKIP_BYTES)
        if len(rot):
            dbytes.write_bytes(S_FLOAT4.pack(*rot))
        else:
            dbytes.write_bytes(SKIP_BYTES)
        if len(scale):
            dbytes.write_bytes(S_FLOAT3.pack(*scale))
        else:
            dbytes.write_bytes(SKIP_BYTES)


def filter_interesting(sec, prober):
    return sec.content_size and prober.is_section_interesting(sec)


def get_default_container(frag):
    if frag.default_container is not None:
        return frag.default_container
    if (frag.base_container is not None
            and frag.container_versions is not None):
        versions = frag.container_versions
        if isinstance(versions, numbers.Integral):
            versions = [versions]
        return Section(frag.base_container, version=max(versions))
    return None


class Fragment(BytesModel):

    """Represents data within a Section."""

    __slots__ = ('_raw_data', 'container', 'dbytes', 'probers')

    default_container = None
    base_container = None
    container_versions = None

    is_interesting = False

    @classmethod
    def class_tag(cls):
        name = cls.__name__
        if not name.endswith('Fragment'):
            raise Exception(f"Could not get class tag for {cls!r}")
        return name[:-8]

    def __init__(self, dbytes=None, **kw):
        self.probers = kw.pop('probers', DefaultProbers)
        super().__init__(dbytes=dbytes, **kw)

    def _init_defaults(self):
        super()._init_defaults()
        con = get_default_container(self)
        if con is not None:
            self.container = con

    def _read(self, dbytes, container=None, probers=None, child_prober=None):

        """Read data of the Fragment.

        `container`    - Container Section of this Fragment. `dbytes` needs to
                         be positioned at content_start of the section if set.
                         If omitted, it is read from dbytes before reading the
                         Fragment.
        `probers`      - If not None, sets the probers used by this Fragment.
        `child_prober` - Specifies the child object prober name for
                         ObjectFragment. Only accepted here to
                         allow passing it without checking for its type.

        """

        self.dbytes = dbytes
        if probers is not None:
            self.probers = probers
        if container is None:
            container = Section(dbytes, seek_end=False)
        self.container = container
        self.end_pos = container.end_pos
        self._read_section_data(dbytes, container)

    def _write(self, dbytes):
        con = getattr(self, 'container', None)
        sec = self._get_write_section(con)
        with dbytes.write_section(sec):
            self._write_section_data(dbytes, sec)

    def _get_write_section(self, sec):
        return sec or self.default_container

    @property
    def raw_data(self):
        try:
            return self._raw_data
        except AttributeError:
            pass
        dbytes = self.dbytes
        sec = self.container
        with dbytes:
            dbytes.seek(sec.content_start)
            data = dbytes.read_bytes(sec.content_size)
            self._raw_data = data
        return data

    @raw_data.setter
    def raw_data(self, value):
        self._raw_data = value

    def clone(self):
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
        pass

    def _write_section_data(self, dbytes, sec):

        """Write data of the given section.

        The default implementation just writes this object's raw_data.

        """

        dbytes.write_bytes(self.raw_data)

    def __str__(self):
        from io import StringIO
        sio = StringIO()
        flags = ('allprops', 'sections', 'transform', 'offset',
                 'objects', 'subobjects', 'groups', 'fragments')
        self.print_data(file=sio, flags=flags)
        return sio.getvalue()

    def _print_type(self, p):
        name = type(self).__name__
        if name.endswith('Fragment'):
            name = name[:-8]
            if not name and type(self) == Fragment:
                p(f"Fragment: Unknown")
            else:
                p(f"Fragment: {name}")

    def _print_data(self, p):
        if 'sections' in p.flags:
            try:
                container = self.container
            except AttributeError:
                pass
            else:
                p(f"Container:")
                with p.tree_children():
                    p.print_data_of(container)


@Probers.base_fragments.fragment
@Probers.fragments.fragment
class ObjectFragment(Fragment):

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
        self._child_prober = getattr(self.probers, kw['child_prober'])
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

    def _write_section_data(self, dbytes, sec):
        transform = self.real_transform
        children = self.children
        has_children = self.has_children or children
        if transform or has_children:
            transform.write_to(dbytes)
        if has_children:
            with dbytes.write_section(Magic[5]):
                for obj in children:
                    obj.write(dbytes)


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

    @classmethod
    def add_to(cls, target, *classes):
        if not all(callable(c) for c in classes):
            raise TypeError("Not all args are callable")
        cls.add_sections_to(target, *(con for con in map(get_default_container, classes)
                                      if con is not None))

    @staticmethod
    def add_sections_to(target, *sections):
        try:
            registered = target.__sections
        except AttributeError:
            registered = []
        target.__sections = registered + [s for s in sections
                                          if s not in registered]

    @staticmethod
    def get_sections(target):
        return target.__sections

    def __init__(self, *classes):
        self.classes = classes

    def __call__(self, target):
        self.add_to(target, *self.classes)
        return target


class MappedSequenceView(collections.Sequence):

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
    return MappedSequenceView(frags, attrgetter('container'))


@default_fragments(ObjectFragment)
class BaseObject(Fragment):

    """Represents data within a Magic[6] Section."""

    __slots__ = ('type', '_sections', '_fragments')

    child_prober_name = 'base_objects'
    is_object_group = False
    has_children = False

    default_transform = None

    @classmethod
    def class_tag(cls):
        return getattr(cls, 'type', cls.__name__)

    def __init__(self, *args, **kw):
        container = kw.get('container')
        if container is not None:
            self.type = container.type
        super().__init__(*args, **kw)

    real_transform = _object_property('real_transform', default=Transform())

    children = _object_property('children', default=())

    @property
    def transform(self):
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
                         doc="Fragments of this object.")

    @fragments.setter
    def fragments(self, value):
        self._sections = _FragmentsContainerView(value)
        self._fragments = value

    sections = property(attrgetter('_sections'),
                        doc=("Containers of the fragments of this object."
                             " (read-only view of fragments*.container)"))

    def fragment_by_type(self, typ):
        probe = self.probers.fragments.probe_section
        i = 0
        for sec in self.sections:
            sec_typ = probe(sec)
            if issubclass(sec_typ, typ):
                return self.fragments[i]
            i += 1
        return None

    def filtered_fragments(self, type_filter):
        fragments = self._fragments
        prober = self.probers.fragments
        i = 0
        for sec in self._sections:
            if type_filter(sec, prober):
                yield fragments[i]
            i += 1

    def __getitem__(self, tag):
        """Get fragment with given tag, if implemented.

        Raises
        ------
        FragmentKeyError (a KeyError)
            If fragment is not present or not implemented.
        """

        base_key, versions = self.probers.fragments.get_tag_impl_info(tag)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                if (versions != 'all' and sec.has_version()
                        and sec.version not in versions):
                    raise FragmentKeyError(tag, sec.version)
                return self.fragments[i]
            i += 1
        raise FragmentKeyError(tag)

    def __setitem__(self, tag, frag):
        base_key = self.probers.fragments.base_container_key(tag)
        if frag.container.to_key(noversion=True) != base_key:
            raise KeyError(f"Invalid fragment container: expected"
                           f" {base_key!r} but got {frag.container!r}")
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
        base_key = self.probers.fragments.base_container_key(tag)
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
        "Check whether a fragment with given tag is present and implemented."
        base_key, versions = self.probers.fragments.get_tag_impl_info(tag)
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                return (versions == 'all' or not sec.has_version()
                        or sec.version in versions)
        return False

    def __iter__(self):
        "Not iterable. Implemented only to prevent __getitem__ iteration."
        raise TypeError(f"{type(self).__name__!r} object is not iterable")

    def get_any(self, tag):
        "Get fragment with given tag, regardless of implementation."
        base_key = self.probers.fragments.base_container_key(tag)
        i = 0
        for sec in self.sections:
            if sec.to_key(noversion=True) == base_key:
                return self.fragments[i]
            i += 1
        return None

    def has_any(self, tag):
        "Check whether a fragment with given tag is present."
        base_key = self.probers.fragments.base_container_key(tag)
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
        probers = self.probers
        return probers.fragments.maybe(
            dbytes, probe_section=sec,
            child_prober=self.child_prober_name,
            probers=probers)

    def _get_write_section(self, sec):
        try:
            cid = sec.id
        except AttributeError:
            cid = None
        return Section(Magic[6], self.type, id=cid)

    def _write_section_data(self, dbytes, sec):
        for frag in self._fragments:
            frag.write(dbytes)

    def _init_defaults(self):
        super()._init_defaults()
        sections = [sec for sec in default_fragments.get_sections(self)
                    if sec is not None]
        fragments = []
        for sec in sections:
            cls = self.probers.fragments.probe_section(sec)
            frag = cls(container=sec)
            if cls is ObjectFragment:
                frag.has_children = self.has_children
            fragments.append(frag)
        self.fragments = fragments

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _repr_detail(self):
        supstr = super()._repr_detail()
        return f" type={self.type!r}{supstr}"

    def _print_type(self, p):
        p(f"Object type: {self.type!r}")

    def _print_data(self, p):
        Fragment._print_data(self, p)
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.real_transform)}")
        if 'fragments' in p.flags and self._fragments:
            if 'allprops' in p.flags:
                p(f"Fragments: {len(self._fragments)}")
                with p.tree_children():
                    for frag in self._fragments:
                        p.tree_next_child()
                        p.print_data_of(frag)
            else:
                frags = self.filtered_fragments(filter_interesting)
                try:
                    frag = next(frags)
                except StopIteration:
                    pass
                else:
                    p(f"Fragments: {len(self._fragments)} <filtered>")
                    with p.tree_children():
                        p.tree_next_child()
                        p.print_data_of(frag)
                        for frag in frags:
                            p.tree_next_child()
                            p.print_data_of(frag)

    def _print_children(self, p):
        if self.children:
            num = len(self.children)
            p(f"Children: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


def require_type(*args, func=None):

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
