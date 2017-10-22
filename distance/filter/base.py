

from distance.level import Level
from distance.levelobjects import Group


class ObjectFilter(object):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument("--maxrecurse", type=int, default=-1,
                            help="Maximum of recursions.")

    def __init__(self, name, args):
        self.name = name
        self.maxrecurse = args.maxrecurse

    def filter_object(self, obj):
        return obj,

    def filter_group(self, grp, levels, **kw):
        orig_empty = not grp.children
        grp.children = self.filter_objects(grp.children, levels, **kw)
        if not orig_empty and not grp.children:
            # remove empty group
            return ()
        return grp,

    def filter_any_object(self, obj, levels, **kw):
        if obj.is_object_group:
            if levels == 0:
                return obj,
            return self.filter_group(obj, levels - 1, **kw)
        else:
            return self.filter_object(obj, **kw)

    def filter_objects(self, objects, levels, **kw):
        res = []
        for obj in objects:
            res.extend(self.filter_any_object(obj, levels, **kw))
        return res

    def apply_level(self, level):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects, self.maxrecurse)

    def apply_group(self, grp):
        # not using filter_group, because we never want to remove the root
        # group object
        grp.children = self.filter_objects(grp.children, self.maxrecurse)

    def apply(self, content):
        if isinstance(content, Level):
            self.apply_level(content)
        elif isinstance(content, Group):
            self.apply_group(content)
        else:
            raise TypeError(f'Unknown object type: {type(content).__name__!r}')

    def post_filter(self, content):
        return True

    def print_summary(self, p):
        pass


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
