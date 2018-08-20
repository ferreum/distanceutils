"""Level file support."""


from .bytes import Magic, Section
from .base import Fragment
from .lazy import LazySequence
from .printing import need_counters
from .classes import CollectorGroup, DefaultClasses


Classes = CollectorGroup()


fragment_attrs = DefaultClasses.fragments.fragment_attrs


@Classes.level.fragment
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

        self.content = self.classes.level_content.lazy_n_maybe(
            dbytes, num_layers + 1)
        if num_layers:
            self.layers = LazySequence(
                (obj for obj in self.content if obj.class_tag == 'Layer'),
                num_layers)

    def _get_write_section(self, sec):
        return Section(Magic[9], self.name, len(self.layers), self.version)

    def _visit_write_section_data(self, dbytes, sec):
        if sec.magic != Magic[9]:
            raise ValueError(f"Unexpected section: {sec.magic}")
        for obj in self.content:
            yield obj.visit_write(dbytes)

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

    def _repr_detail(self):
        supstr = super()._repr_detail()
        if self.name:
            return f" {self.name!r}{supstr}"
        return supstr

    def visit_print(self, p):
        with need_counters(p) as counters:
            yield super().visit_print(p)
            if counters:
                counters.print(p)

    def _print_type(self, p):
        p(f"Level: {self.name!r} version {self.version}")

    def _visit_print_data(self, p):
        yield super()._visit_print_data(p)
        p(f"Level name: {self.name!r}")

    def _visit_print_children(self, p):
        if self.settings is not None:
            with p.tree_children(1):
                yield self.settings.visit_print(p)
        for layer in self.layers:
            yield layer.visit_print(p)


# vim:set sw=4 ts=8 sts=4 et:
