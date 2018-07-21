"""Level objects."""


from .bytes import Magic
from .base import BaseObject


class LevelObject(BaseObject):

    __slots__ = ()

    child_prober_name = 'level_subobjects'

    has_children = True

    def _print_children(self, p):
        if 'subobjects' in p.flags and self.children:
            num = len(self.children)
            p(f"Subobjects: {num}")
            with p.tree_children():
                for obj in self.children:
                    p.tree_next_child()
                    p.print_data_of(obj)


class SubObject(LevelObject):

    __slots__ = ()

    def _print_type(self, p):
        container = self.container
        if container and container.magic == Magic[6]:
            type_str = container.type
            p(f"Subobject type: {type_str!r}")


def print_objects(p, gen):
    counters = p.counters
    for obj in gen:
        p.tree_next_child()
        counters.num_objects += 1
        if 'numbers' in p.flags:
            p(f"Level object: {counters.num_objects}")
        p.print_data_of(obj)


# vim:set sw=4 ts=8 sts=4 et:
