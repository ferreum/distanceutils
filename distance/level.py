"""Level and level object (CustomObject) support."""


from .bytes import Magic, Section
from .base import Fragment
from .lazy import LazySequence
from .printing import need_counters
from .prober import ProberGroup
from ._default_probers import DefaultProbers


Probers = ProberGroup()


fragment_attrs = DefaultProbers.fragments.fragment_attrs


@Probers.level.fragment
class Level(Fragment):

    class_tag = 'Level'
    default_container = Section(Magic[9])

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
                (obj for obj in self.content if obj.class_tag == 'Layer'),
                num_layers)

    def _get_write_section(self, sec):
        return Section(Magic[9], self.name, len(self.layers), self.version)

    def _write_section_data(self, dbytes, sec):
        if sec.magic != Magic[9]:
            raise ValueError(f"Unexpected section: {sec.magic}")
        for obj in self.content:
            obj.write(dbytes)

    @property
    def settings(self):
        try:
            return self._settings
        except AttributeError:
            for obj in self.content:
                if obj.class_tag != 'Layer':
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
        supstr = super()._repr_detail()
        if self.name:
            return f" {self.name!r}{supstr}"
        return supstr

    def _print_data(self, p):
        super()._print_data(p)
        p(f"Level name: {self.name!r}")
        settings = self.settings
        with p.tree_children():
            p.print_data_of(settings)
        with need_counters(p) as counters:
            for layer in self.layers:
                p.print_data_of(layer)
            if counters:
                counters.print_data(p)


# vim:set sw=4 ts=8 sts=4 et:
