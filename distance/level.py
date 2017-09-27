"""Level and level object (CustomObject) support."""


from struct import Struct

from .bytes import BytesModel, S_FLOAT, MAGIC_2, MAGIC_7, MAGIC_8, MAGIC_9
from .base import BaseObject
from .constants import Difficulty, Mode, AbilityToggle, LAYER_FLAG_NAMES
from .printing import format_duration, need_counters
from .levelobjects import PROBER, print_objects


S_ABILITIES = Struct("5b")


def format_layer_flags(gen):
    for flag, names in gen:
        name = names.get(flag, f"Unknown({flag})")
        if name:
            yield name


class LevelSettings(BaseObject):

    type = None
    version = None
    name = None
    skybox_name = None
    modes = ()
    medal_times = ()
    medal_scores = ()
    abilities = ()
    difficulty = None

    def _read(self, dbytes):
        sec = self._get_start_section()
        if sec.magic == MAGIC_8:
            # Levelinfo section only found in old (v1) maps
            self.type = 'Section 88888888'
            self._report_end_pos(sec.data_start + sec.data_size)
            self._add_unknown(4)
            self.skybox_name = dbytes.read_str()
            self._add_unknown(143)
            self.name = dbytes.read_str()
            return
        BaseObject._read(self, dbytes)

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x52):
            self.version = version = sec.version

            self._add_unknown(8)
            self.name = dbytes.read_str()
            self._add_unknown(4)
            self.modes = modes = {}
            num_modes = dbytes.read_int(4)
            for i in range(num_modes):
                mode = dbytes.read_int(4)
                modes[mode] = dbytes.read_byte()
            self.music_id = dbytes.read_int(4)
            if version <= 3:
                self.skybox_name = dbytes.read_str()
                self._add_unknown(57)
            elif version == 4:
                self._add_unknown(141)
            elif version == 5:
                self._add_unknown(172)
            elif 6 <= version:
                # confirmed only for v6..v9
                self._add_unknown(176)
            self.medal_times = times = []
            self.medal_scores = scores = []
            for i in range(4):
                times.append(dbytes.read_struct(S_FLOAT)[0])
                scores.append(dbytes.read_int(4, signed=True))
            if version >= 1:
                self.abilities = dbytes.read_struct(S_ABILITIES)
            if version >= 2:
                self.difficulty = dbytes.read_int(4)
            return False
        return BaseObject._read_section_data(self, dbytes, sec)

    def _print_type(self, p):
        BaseObject._print_type(self, p)
        if self.version is not None:
            p(f"Object version: {self.version}")

    def _print_data(self, p):
        if self.name is not None:
            p(f"Level name: {self.name!r}")
        if self.skybox_name is not None:
            p(f"Skybox name: {self.skybox_name!r}")
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


class Layer(BytesModel):

    layer_name = None
    layer_flags = (0, 0, 0)
    objects = ()
    has_layer_flags = True
    flags_version = 1
    unknown_flag = 0
    obj_prober = PROBER

    def _handle_opts(self, opts):
        BytesModel._handle_opts(self, opts)
        try:
            self.obj_prober = opts['level_obj_prober']
        except KeyError:
            pass

    def _read(self, dbytes):
        s7 = self._get_start_section()
        if s7.magic != MAGIC_7:
            raise ValueError(f"Invalid layer section: {s7.magic}")
        self._report_end_pos(s7.data_end)

        self.layer_name = s7.layer_name

        pos = dbytes.pos
        if pos + 4 >= s7.data_end:
            # Happens with empty old layer sections, this prevents error
            # with empty layer at end of file.
            self.has_layer_flags = False
            return
        version = dbytes.read_int(4)
        if version == 0 or version == 1:
            self.flags_version = version
            flags = dbytes.read_struct("bbb")
            if version == 0:
                frozen = 1 if flags[0] == 0 else 0
                self.layer_flags = (flags[1], frozen, flags[2])
            else:
                self.layer_flags = flags
                self.unknown_flag = dbytes.read_byte()
        else:
            self.has_layer_flags = False
            # We read start of first object - need to rewind.
            dbytes.pos = pos

        self.objects = self.obj_prober.lazy_n_maybe(dbytes, s7.num_objects, opts=self.opts)

    def write(self, dbytes):
        with dbytes.write_section(MAGIC_7, self.layer_name, len(self.objects)):
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


class Level(BytesModel):

    _settings = None
    layers = ()
    level_name = None
    num_layers = 0
    settings_start = None

    def _read(self, dbytes):
        sec = self._get_start_section()
        if sec.magic != MAGIC_9:
            raise IOError(f"Unexpected section: {sec.magic}")
        self._report_end_pos(sec.data_end)
        self.level_name = sec.level_name
        self.num_layers = sec.num_layers
        self.settings_start = dbytes.pos

        self.layers = Layer.lazy_n_maybe(dbytes, sec.num_layers,
                                         start_pos=self.__get_layers_start,
                                         opts=self.opts)

    def write(self, dbytes):
        with dbytes.write_section(MAGIC_9, self.level_name, len(self.layers)):
            self.settings.write(dbytes)
            for layer in self.layers:
                layer.write(dbytes)

    @property
    def settings(self):
        s = self._settings
        if s is None:
            dbytes = self.dbytes
            with dbytes.saved_pos(self.settings_start):
                self._settings = s = LevelSettings.maybe(self.dbytes)
        return s

    @settings.setter
    def settings(self, s):
        self._settings = s

    def __get_layers_start(self):
        settings = self.settings
        if settings.sane_end_pos:
            return settings.reported_end_pos
        else:
            raise settings.exception

    def iter_objects(self, with_layers=False, with_objects=True):
        for layer in self.layers:
            if with_layers:
                yield layer
            if with_objects:
                yield from layer.objects

    def _print_data(self, p):
        p(f"Level name: {self.level_name!r}")
        try:
            settings = self.settings
            p.print_data_of(settings)
            if not settings.sane_end_pos:
                return
            with need_counters(p) as counters:
                for layer in self.layers:
                    p.print_data_of(layer)
                if counters:
                    counters.print_data(p)
        except Exception as e:
            p.print_exception(e)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
