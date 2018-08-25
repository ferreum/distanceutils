"""Facilities for defining fragments with the construct module."""


from construct import (
    PascalString, VarInt, Bytes, GreedyBytes,
    ConstructError,
    Const, Select, FocusedSeq, Tell,
    Mapping, IfThenElse,
    Compiled, Construct,
    Container,
    this,

    Struct,
    Default,
    Byte,
    Int32sl as Int,
    Int32ul as UInt,
    Int64sl as Long,
    Int64ul as ULong,
    Float32l as Float,
    Float64l as Double,
)

from distance.base import Fragment
from distance.bytes import Magic, SKIP_BYTES
from distance.printing import format_bytes_multiline

__all__ = [
    'BaseConstructFragment',
    'Byte', 'Int', 'UInt', 'Long', 'ULong', 'Float', 'Double', 'DstString',
    'DstOptional', 'Remainder',
    'Struct', 'Default',
]


DstString = PascalString(VarInt, encoding='utf-16le')

def DstOptional(subcon, otherwise=None):
    return Select(
        Mapping(Const(SKIP_BYTES), {otherwise: SKIP_BYTES}),
        subcon)

Remainder = FocusedSeq(
    'rem',
    'pos' / Tell,
    'rem' / IfThenElse(this._parsing,
                       Bytes(this._params.sec.end_pos - this.pos),
                       GreedyBytes),
)


_magic_consts = {k: Const(Magic[k], UInt) for k, v in Magic.items()}
MagicConst = _magic_consts.__getitem__


def _get_subcons(con):
    try:
        return con.subcons
    except AttributeError:
        pass

    try:
        return _get_subcons(con.subcon)
    except AttributeError:
        pass

    if isinstance(con, Compiled):
        return _get_subcons(con.defersubcon)

    raise AttributeError(f"could not get subcons of {con}")


class ConstructMeta(type):

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        if cls._construct_ is not None:
            attrs = {}
            for con in _get_subcons(cls._construct_):
                if con.name:
                    default = getattr(con, 'value', None)
                    # The Default construct provides the default value via its
                    # 'value' attribute. For nested structs, if there is a
                    # 'value' subcon, we instead get that subcon via the attr.
                    # Exclude Construct instances to work around this.
                    if isinstance(default, Construct):
                        default = None
                    attrs[con.name] = default
            add = getattr(cls, '_add_fields_', None)
            if add:
                attrs.update(add)
            cls._fields_ = attrs

            ExposeConstructFields(cls, getattr(cls, '_exposed_fields_', None))


class BaseConstructFragment(Fragment, metaclass=ConstructMeta):

    """Baseclass for fragments defined by construct Structs.

    Subclasses need to override the `_construct_` attribute with the Struct that
    defines the fragment.

    """

    __slots__ = ('data',)

    # to be overridden by subclasses
    _construct_ = None

    def _init_defaults(self):
        super()._init_defaults()
        self.data = Container()

    def _clone_data(self, new):
        new.data = Container(self.data)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            try:
                self.data = self._construct_.parse_stream(dbytes.file, sec=sec)
            except ConstructError as e:
                self.data = Container()
                raise ValueError from e
            except:
                self.data = Container()
                raise
        else:
            # Data is empty - game falls back to defaults here.
            self.data = Container()

    def _write_section_data(self, dbytes, sec):
        # If data is empty, game falls back to defaults.
        if self.data:
            self._construct_.build_stream(self.data, dbytes.file, sec=sec)

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        if 'allprops' in p.flags:
            items = [(k, v) for k, v in self.data.items() if k != '_io']
            p(f"Fields: {len(items)}")
            with p.tree_children(len(items)):
                indent = "        "
                for name, value in items:
                    if name != '_io': # construct internal?
                        p.tree_next_child()
                        if isinstance(value, bytes):
                            lines = format_bytes_multiline(value)
                        else:
                            lines = str(value).splitlines()
                        lines = lines or ["<empty>"]
                        if len(lines) > 1:
                            p(f"Field: {name} =")
                            for line in lines:
                                p(indent + line)
                        else:
                            p(f"Field: {name} = " + lines[0])


def construct_property(cls, name, doc=None):
    if doc is None:
        doc = f"property forwarded to construct field {name!r}"
    def fget(self):
        try:
            return self.data[name]
        except KeyError as e:
            try:
                return cls._fields_[name]
            except KeyError:
                pass
            raise AttributeError from e
    def fset(self, value):
        self.data[name] = value
    def fdel(self):
        try:
            del self.data[name]
        except KeyError as e:
            raise AttributeError from e
    return property(fget, fset, fdel, doc=doc)


def ExposeConstructFields(target=None, only=None):

    """Decorator to expose construct fields as attributes."""

    def decorate(target):
        subcons = _get_subcons(target._construct_)
        if only is None:
            cons = (c for c in subcons if isinstance(c.name, str))
            names = ()
        else:
            names = set([only] if isinstance(only, str) else only)
            def pop_name(con):
                if con.name in names:
                    names.remove(con.name)
                    return True
                return False
            cons = filter(pop_name, subcons)
        for con in cons:
            doc = getattr(con, 'docs', None)
            if not isinstance(doc, str) or not doc:
                doc = None
            setattr(target, con.name, construct_property(target, con.name, doc=doc))
        if names:
            raise AttributeError(f"{target.__name__} has no attributes {names!r}")
        return target

    if target is None:
        return decorate
    return decorate(target)


# vim:set sw=4 ts=8 sts=4 et:
