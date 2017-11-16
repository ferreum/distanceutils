"""Base classes for filters."""


from distance.base import Transform, TransformError
from distance.level import Level
from distance.levelobjects import Group
from distance import levelfragments as levelfrags


ANIM_FRAG_TYPES = (
    levelfrags.AnimatorFragment,
    levelfrags.EventListenerFragment,
    levelfrags.TrackAttachmentFragment,
)

def create_replacement_group(orig, objs, animated_only=False):
    copied_frags = []
    for ty in ANIM_FRAG_TYPES:
        copyfrag = orig.fragment_by_type(ty)
        if copyfrag is not None:
            copied_frags.append(copyfrag.clone())
    if animated_only and not copied_frags:
        return objs
    pos, rot, scale = orig.transform
    group = Group(children=objs)
    group.recenter(pos)
    group.rerotate(rot)
    group.rescale(scale)
    group.fragments = list(group.fragments) + copied_frags
    return group,


class ObjectFilter(object):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(":maxrecurse", type=int, default=-1,
                            help="Set recursion limit, -1 for infinite (the default).")

    def __init__(self, args):
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

    def apply_level(self, level, **kw):
        for layer in level.layers:
            layer.objects = self.filter_objects(layer.objects, self.maxrecurse, **kw)

    def apply_group(self, grp, **kw):
        # not using filter_group, because we never want to remove the root
        # group object
        grp.children = self.filter_objects(grp.children, self.maxrecurse, **kw)

    def apply(self, content, **kw):
        if isinstance(content, Level):
            self.apply_level(content, **kw)
        elif isinstance(content, Group):
            self.apply_group(content, **kw)
        else:
            raise TypeError(f'Unknown object type: {type(content).__name__!r}')

    def post_filter(self, content):
        return True

    def print_summary(self, p):
        pass


class DoNotApply(Exception):

    def __init__(self, reason=None, *args, **kw):
        super().__init__(*args, **kw)
        self.reason = reason


class ObjectMapper(object):

    def __init__(self, pos=(0, 0, 0), rot=(0, 0, 0, 1), scale=(1, 1, 1)):
        self.transform = Transform.fill(pos=pos, rot=rot, scale=scale)

    def _apply_transform(self, transform, global_transform=Transform.fill()):
        try:
            res = transform.apply(*self.transform)
        except TransformError:
            raise DoNotApply('locked_scale')
        try:
            # raises TransformError if we are inside groups with
            # incompatible scale
            global_transform.apply(*res)
        except TransformError:
            raise DoNotApply('locked_scale_group')
        return res

    def apply(self, obj, global_transform=Transform.fill(), **kw):
        transform = self._apply_transform(obj.transform,
                                          global_transform=global_transform)

        return self.create_result(obj, transform, **kw)

    def create_result(self, old, transform):
        raise NotImplementedError


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
