"""Provides BaseObject."""


from operator import itemgetter, attrgetter
import numbers
import collections

from .bytes import (BytesModel, Section, MAGIC_3, MAGIC_5, MAGIC_6,
                    SKIP_BYTES, S_FLOAT3, S_FLOAT4)
from .printing import format_transform
from .prober import BytesProber, ProbeError
from .lazy import LazySequence, LazyMappedSequence


BASE_PROBER = BytesProber()

BASE_FRAG_PROBER = BytesProber()

EMPTY_PROBER = BytesProber()

TRANSFORM_MIN_SIZE = 12


class TransformError(ValueError):
    pass


class NoDefaultTransformError(TypeError):
    pass


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
    return sec.content_size and prober.probe_section(sec).is_interesting


class Fragment(BytesModel):

    """Represents data within a Section."""

    __slots__ = ('_raw_data', 'container', 'dbytes')

    default_section = None

    is_interesting = False

    def _init_defaults(self):
        super()._init_defaults()
        con = self.default_section
        if con is not None:
            self.container = con

    def _read(self, dbytes, container=None, **kw):
        self.dbytes = dbytes
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
        return sec or self.default_section

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


@BASE_FRAG_PROBER.fragment(MAGIC_3, 1, 0)
class ObjectFragment(Fragment):

    __slots__ = ('real_transform', 'has_children', 'children',
                 '_child_prober')

    default_section = Section(MAGIC_3, 1, 0)

    def _init_defaults(self):
        super()._init_defaults()
        self.real_transform = Transform()
        self.has_children = False
        self.children = ()

    def _read(self, *args, **kw):
        self._child_prober = kw.get('child_prober', EMPTY_PROBER)
        Fragment._read(self, *args, **kw)

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
            with dbytes.write_section(MAGIC_5):
                for obj in children:
                    obj.write(dbytes)


def fragment_property(cls, name, default=None, doc=None):
    if doc is None:
        doc = f"property forwarded to {cls.__name__!r}"
    def fget(self):
        frag = self.fragment_by_type(cls)
        return getattr(frag, name, default)
    def fset(self, value):
        frag = self.fragment_by_type(cls)
        setattr(frag, name, value)
    return property(fget, fset, None, doc=doc)


class ForwardFragmentAttrs(object):

    """Decorator to forward attributes of objects to their fragments."""

    def __init__(self, cls, **attrs):
        self.cls = cls
        self.attrs = attrs

    def __call__(self, target):
        cls = self.cls
        for name, default in self.attrs.items():
            setattr(target, name, fragment_property(cls, name, default))
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


@ForwardFragmentAttrs(ObjectFragment, real_transform=Transform(), children=())
class BaseObject(Fragment):

    """Represents data within a MAGIC_6 Section."""

    __slots__ = ('type', '_sections', '_fragments',
                 '_fragment_types', '_fragments_by_type')

    child_prober = BASE_PROBER
    fragment_prober = BASE_FRAG_PROBER
    is_object_group = False
    has_children = False

    default_sections = (
        Section(MAGIC_3, 0x01, 0),
    )
    default_transform = None

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
        self._fragment_types = MappedSequenceView(value, type)
        self._fragments_by_type = {}

    sections = property(attrgetter('_sections'),
                        doc=("Containers of the fragments of this object."
                             " (read-only view of fragments*.container)"))

    def fragment_by_type(self, typ):
        if typ is ObjectFragment:
            # Optimized ObjectFragment access: it is virtually always first.
            try:
                frag = self._fragments[0]
            except IndexError:
                pass # empty fragments
            else:
                if type(frag) is ObjectFragment:
                    return frag
            # not first - fall through to regular method
        try:
            bytype = self._fragments_by_type
        except AttributeError:
            probe = self.fragment_prober.probe_section
            secs = self._sections
            types = LazySequence(map(probe, secs), len(secs))
            bytype = {}
            self._fragment_types = types
            self._fragments_by_type = bytype
        else:
            try:
                return bytype[typ]
            except KeyError:
                types = self._fragment_types
                # not cached, fall through
        i = 0
        for sectype in types:
            if issubclass(sectype, typ):
                frag = self._fragments[i]
                bytype[typ] = frag
                return frag
            i += 1
        bytype[typ] = None
        return None

    def filtered_fragments(self, type_filter):
        fragments = self._fragments
        prober = self.fragment_prober
        i = 0
        for sec in self._sections:
            if type_filter(sec, prober):
                yield fragments[i]
            i += 1

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
        return self.fragment_prober.maybe(
            dbytes, probe_section=sec,
            child_prober=self.child_prober)

    def _get_write_section(self, sec):
        try:
            cid = sec.id
        except AttributeError:
            cid = None
        return Section(MAGIC_6, self.type, id=cid)

    def _write_section_data(self, dbytes, sec):
        for frag in self._fragments:
            frag.write(dbytes)

    def _init_defaults(self):
        super()._init_defaults()
        sections = list(Section(s) for s in self.default_sections)
        fragments = []
        for sec in sections:
            try:
                cls = self.fragment_prober.probe_section(sec)
            except ProbeError:
                pass # subclass has to write this section
            else:
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
                    p(f"Fragments: {len(self._fragments)} <filtered>")
                    with p.tree_children():
                        p.tree_next_child()
                        p.print_data_of(frag)
                        for frag in frags:
                            p.tree_next_child()
                            p.print_data_of(frag)
                except StopIteration:
                    pass

    def _print_children(self, p):
        if self.children:
            num = len(self.children)
            p(f"Children: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


def require_type(typ):
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
    return decorate


@BASE_PROBER.func
def _probe_fallback(sec):
    if sec.magic == MAGIC_6:
        return BaseObject
    return None


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
