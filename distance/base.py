"""Provides BaseObject."""


from operator import itemgetter
import numbers

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

    default_section = None

    is_interesting = False

    _raw_data = None

    def _read(self, dbytes, **kw):
        sec = self._get_container()
        self.end_pos = sec.end_pos
        self._read_section_data(dbytes, sec)

    def _write(self, dbytes):
        sec = getattr(self, 'container', None)
        if sec is None:
            self.container = sec = self._init_section()
        with dbytes.write_section(sec):
            self._write_section_data(dbytes, sec)

    @property
    def raw_data(self):
        data = self._raw_data
        if data is None:
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
        if self.container:
            new.container = Section(self.container)
        self._clone_data(new)
        return new

    def _clone_data(self, new):
        new.raw_data = self.raw_data

    def _init_section(self):
        return self.default_section

    def _read_section_data(self, dbytes, sec):
        """Read data of the given section."""
        pass

    def _write_section_data(self, dbytes, sec):

        """Write data of the given section.

        The default implementation just writes this fragment's raw_data.

        """

        dbytes.write_bytes(self.raw_data)

    def _print_type(self, p):
        name = type(self).__name__
        if name.endswith('Fragment'):
            name = name[:-8]
            if not name and type(self) == Fragment:
                p(f"Fragment: Unknown")
            else:
                p(f"Fragment: {name}")


@BASE_FRAG_PROBER.fragment(MAGIC_3, 1, 0)
class ObjectFragment(Fragment):

    real_transform = Transform()
    has_children = False
    children = ()

    def _read(self, *args, **kw):
        self.child_prober = kw.get('child_prober', EMPTY_PROBER)
        Fragment._read(self, *args, **kw)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size >= TRANSFORM_MIN_SIZE:
            self.real_transform = Transform.read_from(dbytes)
            if dbytes.tell() + Section.MIN_SIZE < sec.end_pos:
                s5 = Section(dbytes, seek_end=False)
                self.has_children = True
                self.children = self.child_prober.lazy_n_maybe(
                    dbytes, s5.count, opts=self.opts,
                    start_pos=s5.content_start)

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


class ForwardFragmentAttrs(object):

    """Decorator to forward attributes of objects to their fragments."""

    def __init__(self, cls, **attrs):
        self.cls = cls
        self.attrs = attrs

    def __call__(self, target):
        cls = self.cls
        doc = f"property forwarded to {cls.__name__!r}"
        for name, default in self.attrs.items():
            # These keyword args are here to capture the values of every
            # iteration. Otherwise they would all refer to the same variable
            # which is set to the value of the last iteration.
            def fget(self, name=name, default=default):
                frag = self.fragment_by_type(cls)
                return getattr(frag, name, default)
            def fset(self, value, name=name):
                frag = self.fragment_by_type(cls)
                setattr(frag, name, value)
            setattr(target, name, property(fget, fset, None, doc=doc))
        return target


@ForwardFragmentAttrs(ObjectFragment, real_transform=Transform(), children=())
class BaseObject(BytesModel):

    """Base class of objects represented by a MAGIC_6 section."""

    child_prober = BASE_PROBER
    fragment_prober = BASE_FRAG_PROBER
    is_object_group = False

    sections = ()
    fragments = ()
    _fragment_types = None
    _fragments_by_type = None

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

    def fragment_by_type(self, typ):
        if typ is ObjectFragment:
            # Optimized ObjectFragment access: it is virtually always first.
            frag = self.fragments[0]
            if type(frag) is ObjectFragment:
                return frag
            # not first - fall through to regular method
        types = self._fragment_types
        if types is None:
            probe = self.fragment_prober.probe_section
            secs = self.sections
            types = LazySequence(map(probe, secs), len(secs))
            bytype = {}
            self._fragments_by_type = bytype
        else:
            bytype = self._fragments_by_type
            try:
                return bytype[typ]
            except KeyError:
                pass # not cached, fall through
        i = 0
        for sectype in types:
            if issubclass(sectype, typ):
                frag = self.fragments[i]
                bytype[typ] = frag
                return frag
            i += 1
        bytype[typ] = None
        return None

    def filtered_fragments(self, type_filter):
        fragments = self.fragments
        prober = self.fragment_prober
        i = 0
        for sec in self.sections:
            if type_filter(sec, prober):
                yield fragments[i]
            i += 1

    def _read(self, dbytes):
        sec = self._get_container()
        self.type = sec.type
        self.end_pos = sec.end_pos
        self.sections = Section.lazy_n_maybe(dbytes, sec.count)
        self.fragments = LazyMappedSequence(
            self.sections, self._read_fragment)

    def _read_fragment(self, sec):
        if sec.exception:
            # failed to read section - return object containing the error
            return Fragment(exception=sec.exception)
        dbytes = self.dbytes
        dbytes.seek(sec.content_start)
        return self.fragment_prober.maybe(
            dbytes, probe_section=sec,
            child_prober=self.child_prober)

    def _write(self, dbytes):
        try:
            cid = self.container.id
        except AttributeError:
            cid = None
        with dbytes.write_section(MAGIC_6, self.type, id=cid):
            for frag in self.fragments:
                frag.write(dbytes)

    def _init_defaults(self):
        sections = list(Section(s) for s in self.default_sections)
        fragments = []
        self.sections = sections
        self.fragments = fragments
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

    def iter_children(self, ty=None, name=None):
        for obj in self.children:
            if ty is None or isinstance(obj, ty):
                if name is None or obj.type == name:
                    yield obj

    def _print_type(self, p):
        p(f"Object type: {self.type!r}")

    def _print_data(self, p):
        if 'transform' in p.flags:
            p(f"Transform: {format_transform(self.real_transform)}")
        if 'fragments' in p.flags and self.fragments:
            if 'allprops' in p.flags:
                p(f"Fragments: {len(self.fragments)}")
                with p.tree_children():
                    for frag in self.fragments:
                        p.tree_next_child()
                        p.print_data_of(frag)
            else:
                frags = self.filtered_fragments(filter_interesting)
                try:
                    frag = next(frags)
                    p(f"Fragments: {len(self.fragments)} <filtered>")
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


@BASE_PROBER.func
def _probe_fallback(sec):
    if sec.magic == MAGIC_6:
        return BaseObject
    return None


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
