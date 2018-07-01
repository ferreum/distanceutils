"""Level and level object (CustomObject) support."""


from collections import OrderedDict

from construct import (
    Struct, Sequence,
    PrefixedArray, If, Computed,
    Container, ListContainer,
    this, len_,
)

from .bytes import Magic, Section
from .base import (
    BaseObject, Fragment,
    ForwardFragmentAttrs
)
from .construct import (
    BaseConstructFragment,
    Int, UInt, Bytes, Byte, Float,
    DstString, Remainder,
)
from .lazy import LazySequence
from .constants import Difficulty, Mode, AbilityToggle, LAYER_FLAG_NAMES
from .printing import format_duration, need_counters
from .levelobjects import print_objects
from ._default_probers import DefaultProbers


FILE_PROBER = DefaultProbers.file.transaction()
LEVEL_LIKE_PROBER = DefaultProbers.get_or_create('level_like').transaction()
LEVEL_CONTENT_PROBER = DefaultProbers.get_or_create('level_content').transaction()
FRAG_PROBER = DefaultProbers.fragments.transaction()


def format_layer_flags(gen):
    for flag, names in gen:
        name = names.get(flag, f"Unknown({flag})")
        if name:
            yield name


class LevelSettings(object):

    value_attrs = dict(
        version = None,
        name = None,
        description = None,
        author_name = None,
        skybox_name = None,
        modes = (),
        medal_times = (),
        medal_scores = (),
        background_layer = None,
        abilities = (),
        difficulty = None,
    )

    def _print_data(self, p):
        super()._print_data(p)
        if self.name is not None:
            p(f"Level name: {self.name!r}")
        if self.skybox_name is not None:
            p(f"Skybox name: {self.skybox_name!r}")
        if self.background_layer is not None:
            p(f"Background layer: {self.background_layer!r}")
        if self.medal_times:
            medal_str = ', '.join(format_duration(t) for t in self.medal_times)
            p(f"Medal times: {medal_str}")
        if self.medal_scores:
            medal_str = ', '.join(str(s) for s in self.medal_scores)
            p(f"Medal scores: {medal_str}")
        if self.modes:
            modes_str = ', '.join(Mode.to_name(mode)
                                  for mode, value in sorted(self.modes.items())
                                  if value)
            p(f"Level modes: {modes_str or 'None'}")
        if self.abilities:
            ab_str = ', '.join(AbilityToggle.to_name_for_value(toggle, value)
                               for toggle, value in enumerate(self.abilities)
                               if value != 0)
            if not ab_str:
                ab_str = "All"
            p(f"Abilities: {ab_str}")
        if self.difficulty is not None:
            p(f"Difficulty: {Difficulty.to_name(self.difficulty)}")
        if self.author_name:
            p(f"Author: {self.author_name!r}")
        if self.description and 'description' in p.flags:
            p(f"Description: {self.description}")


@FRAG_PROBER.fragment(any_version=True)
class LevelSettingsFragment(BaseConstructFragment):

    base_container = Section.base(Magic[2], 0x52)

    def get_unk_2_size(this):
        version = this.version
        if version <= 3:
            return 57
        elif version == 4:
            return 141
        elif version == 5:
            return 172
        elif 6 <= version < 25:
            # confirmed only for v6..v9
            return 176
        else:
            # confirmed for v25..v26
            return 231

    _construct = Struct(
        version = Computed(this._params.sec.version),
        unk_0 = Bytes(8),
        name = DstString,
        description = If(this.version >= 25, DstString),
        author_name = If(this.version >= 25, DstString),
        unk_1 = Bytes(4),
        modes_list = PrefixedArray(UInt, Struct(
            mode = UInt,
            enabled = Byte,
        )),
        music_id = UInt,
        skybox_name = If(this.version <= 3, DstString),
        unk_2 = Bytes(get_unk_2_size),
        # confirmed for v25..26
        background_layer = If(this.version >= 25, DstString),
        # confirmed for v25..26
        unk_3 = If(this.version >= 25, Bytes(61)),
        medals_list = Struct(
            time = Float,
            score = Int,
        )[4],
        abilities = If(this.version >= 1, Sequence(Byte, Byte, Byte, Byte, Byte)),
        difficulty = If(this.version >= 2, UInt),
        unk_4 = Remainder,
    )

    del get_unk_2_size

    @property
    def modes(self):
        d = OrderedDict()
        for elem in self.modes_list:
            d[elem.mode] = elem.enabled
        return d

    @modes.setter
    def modes(self, value):
        l = [Container(mode=k, enabled=v) for k, v in value.items()]
        self.modes_list = ListContainer(l)

    @property
    def medal_times(self):
        return [m.time for m in self.medals_list]

    @medal_times.setter
    def medal_times(self, value):
        if len(value) != 4:
            raise ValueError("Need four medal times")
        l = [Container(time = t, score = m.score)
             for t, m in zip(value, self.medal_list)]
        self.medals_list = ListContainer(l)

    @property
    def medal_scores(self):
        return [m.score for m in self.medals_list]

    @medal_scores.setter
    def medal_scores(self, value):
        if len(value) != 4:
            raise ValueError("Need four medal scores")
        l = [Container(time = m.time, score = s)
             for m, s in zip(self.medal_list, value)]
        self.medals_list = ListContainer(l)


@LEVEL_CONTENT_PROBER.for_type
@ForwardFragmentAttrs(LevelSettingsFragment, **LevelSettings.value_attrs)
class NewLevelSettings(LevelSettings, BaseObject):

    type = 'LevelSettings'

    def _print_type(self, p):
        BaseObject._print_type(self, p)
        if self.version is not None:
            p(f"Object version: {self.version}")


@LEVEL_CONTENT_PROBER.fragment
class OldLevelSettings(LevelSettings, BaseConstructFragment):

    default_container = Section(Magic[8])

    """Special settings section only found in very old maps."""

    # fallbacks for base LevelSettings and other usages
    version = None
    description = None
    author_name = None
    modes = ()
    medal_times = ()
    medal_scores = ()
    background_layer = None
    abilities = ()
    difficulty = None

    _construct = Struct(
        unk_0 = Bytes(4),
        skybox_name = DstString,
        unk_1 = Bytes(143),
        name = DstString,
        unk_2 = Remainder,
    )

    def _print_type(self, p):
        p(f"Type: LevelSettings (old)")


@LEVEL_CONTENT_PROBER.fragment
class Layer(Fragment):

    default_container = Section(Magic[7])

    layer_name = None
    layer_flags = (0, 0, 0)
    objects = ()
    has_layer_flags = True
    flags_version = 1
    unknown_flag = 0

    def _read_section_data(self, dbytes, sec):
        if sec.magic != Magic[7]:
            raise ValueError(f"Invalid layer section: {sec.magic}")
        self.layer_name = sec.name

        if sec.content_size < 4:
            # Happens with empty old layer sections, this prevents error
            # with empty layer at end of file.
            self.has_layer_flags = False
            return
        version = dbytes.read_uint4()
        if version in (0, 1):
            self.flags_version = version
            flags = dbytes.read_bytes(3)
            if version == 0:
                frozen = 1 if flags[0] == 0 else 0
                self.layer_flags = (flags[1], frozen, flags[2])
            else:
                self.layer_flags = flags
                self.unknown_flag = dbytes.read_byte()
            obj_start = dbytes.tell()
        else:
            self.has_layer_flags = False
            obj_start = sec.content_start
        self.objects = self.probers.level_objects.lazy_n_maybe(
            dbytes, sec.count, start_pos=obj_start)

    def _write_section_data(self, dbytes, sec):
        if sec.magic != Magic[7]:
            raise ValueError(f"Invalid layer section: {sec.magic}")
        if self.has_layer_flags:
            flags = self.layer_flags
            dbytes.write_int(4, self.flags_version)
            if self.flags_version == 0:
                dbytes.write_int(1, 0 if flags[1] else 1)
                dbytes.write_int(1, flags[0])
                dbytes.write_int(1, flags[2])
            else:
                dbytes.write_int(1, flags[0])
                dbytes.write_int(1, flags[1])
                dbytes.write_int(1, flags[2])
                dbytes.write_int(1, self.unknown_flag)
        for obj in self.objects:
            obj.write(dbytes)

    def _repr_detail(self):
        supstr = super()._repr_detail()
        return f" {self.layer_name!r}{supstr}"

    def _print_type(self, p):
        p(f"Layer: {self.layer_name!r}")

    def _print_data(self, p):
        with need_counters(p) as counters:
            p(f"Layer object count: {len(self.objects)}")
            if self.layer_flags:
                flag_str = ', '.join(
                    format_layer_flags(zip(self.layer_flags, LAYER_FLAG_NAMES)))
                if not flag_str:
                    flag_str = "None"
                p(f"Layer flags: {flag_str}")
            p.counters.num_layers += 1
            p.counters.layer_objects += len(self.objects)
            with p.tree_children():
                print_objects(p, self.objects)
            if counters:
                counters.print_data(p)


@FILE_PROBER.fragment
@LEVEL_LIKE_PROBER.fragment
class Level(Fragment):

    default_container = Section(Magic[9])

    _settings = Ellipsis
    layers = ()
    name = None
    version = 3

    def _read_section_data(self, dbytes, sec):
        if sec.magic != Magic[9]:
            raise ValueError(f"Unexpected section: {sec.magic}")
        self.name = sec.name
        self.version = sec.version

        num_layers = sec.count

        self.content = self.probers.level_content.lazy_n_maybe(
            dbytes, num_layers + 1)
        if num_layers:
            self.layers = LazySequence(
                (obj for obj in self.content if isinstance(obj, Layer)),
                num_layers)

    def _write(self, dbytes):
        num_layers = len(self.layers)
        with dbytes.write_section(Magic[9], self.name,
                                  num_layers, self.version) as sec:
            self._write_section_data(dbytes, sec)

    def _write_section_data(self, dbytes, sec):
        if sec.magic != Magic[9]:
            raise ValueError(f"Unexpected section: {sec.magic}")
        for obj in self.content:
            obj.write(dbytes)

    @property
    def settings(self):
        s = self._settings
        if s is Ellipsis:
            for obj in self.content:
                if not isinstance(obj, Layer):
                    s = obj
                    break
            else:
                s = None
            self._settings = s
        return s

    @settings.setter
    def settings(self, s):
        self._settings = s

    def iter_objects(self, with_layers=False, with_objects=True):
        for layer in self.layers:
            if with_layers:
                yield layer
            if with_objects:
                yield from layer.objects

    def _repr_detail(self):
        if self.name:
            return f" {self.name!r}"

    def _print_data(self, p):
        p(f"Level name: {self.name!r}")
        try:
            settings = self.settings
            with p.tree_children():
                p.print_data_of(settings)
            with need_counters(p) as counters:
                for layer in self.layers:
                    p.print_data_of(layer)
                if counters:
                    counters.print_data(p)
        except Exception as e:
            p.print_exception(e)


LEVEL_CONTENT_PROBER.commit()
FRAG_PROBER.commit()
LEVEL_LIKE_PROBER.commit()
FILE_PROBER.commit()


# vim:set sw=4 ts=8 sts=4 et:
