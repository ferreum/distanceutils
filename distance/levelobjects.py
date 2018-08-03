"""Level objects."""


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
        p(f"Subobject type: {self.type!r}")


# vim:set sw=4 ts=8 sts=4 et:
