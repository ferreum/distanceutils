"""Facilities for defining fragments with the construct module."""


from construct import (
    PascalString, VarInt, Bytes, GreedyBytes,
    ConstructError,
    Const, Select, FocusedSeq, Tell,
    Mapping, IfThenElse,
    Compiled,
    Container,
    this,
)

from distance.base import Fragment
from distance.bytes import SKIP_BYTES


class C(object):

    """Provides cons useful for distance .bytes files."""

    from construct import (
        Struct as struct,
        Default as default,
        Byte as byte,
        Int32sl as int,
        Int32ul as uint,
        Int64sl as long,
        Int64ul as ulong,
        Float32l as float,
        Float64l as double,
    )

    str = PascalString(VarInt, encoding='utf-16le')

    def optional(subcon, otherwise=None):
        return Select(
            Mapping(Const(SKIP_BYTES), {otherwise: SKIP_BYTES}),
            subcon)

    remainder = FocusedSeq(
        'rem',
        'pos' / Tell,
        'rem' / IfThenElse(this._parsing,
                           Bytes(this._._.sec.content_end - this.pos),
                           GreedyBytes),
    )


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
        if cls._construct is not None:
            attrs = {}
            for con in _get_subcons(cls._construct):
                if con.name:
                    attrs[con.name] = getattr(con, 'value', None)
            cls._fields_map = attrs

            ExposeConstructFields(cls, getattr(cls, '_exposed_fields', None))


class BaseConstructFragment(Fragment, metaclass=ConstructMeta):

    """Baseclass for fragments defined by construct Structs.

    Subclasses need to override the `_construct` attribute with the Struct that
    defines the fragment.

    """

    __slots__ = ('data',)

    # to be overridden by subclasses
    _construct = None

    def _init_defaults(self):
        self.data = Container()

    def _clone_data(self, new):
        new.data = Container(self.data)

    def _read_section_data(self, dbytes, sec):
        if sec.content_size:
            try:
                self.data = self._construct.parse_stream(dbytes.file, sec=sec)
            except ConstructError as e:
                raise ValueError from e
        else:
            # Data is empty - game falls back to defaults here.
            self.data = Container()

    def _write_section_data(self, dbytes, sec):
        # If data is empty, game falls back to defaults.
        if self.data:
            self._construct.build_stream(self.data, dbytes.file, sec=sec)

    def _print_data(self, p):
        super()._print_data(p)
        if 'allprops' in p.flags:
            with p.tree_children():
                for k, v in self.data.items():
                    if k != '_io': # construct internal?
                        p.tree_next_child()
                        p(f"Field: {k} = {v!r}")


def construct_property(cls, name, doc=None):
    if doc is None:
        doc = f"property forwarded to construct field {name!r}"
    def fget(self):
        try:
            return self.data[name]
        except KeyError as e:
            try:
                return cls._fields_map[name]
            except KeyError:
                pass
            raise AssertionError from e
    def fset(self, value):
        self.data[name] = value
    def fdel(self):
        try:
            del self.data[name]
        except KeyError as e:
            raise AssertionError from e
    return property(fget, fset, fdel, doc=doc)


def ExposeConstructFields(target=None, only=None):

    """Decorator to expose construct fields as attributes."""

    def decorate(target):
        if only is None:
            names = (c.name for c in _get_subcons(target._construct) if c.name)
        else:
            names = [only] if isinstance(only, str) else only
        for name in names:
            setattr(target, name, construct_property(target, name))
        return target

    if target is None:
        return decorate
    return decorate(target)


# vim:set sw=4 ts=8 sts=4 et:
