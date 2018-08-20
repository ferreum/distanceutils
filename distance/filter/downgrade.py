"""Filter for downgrading objects"""


from collections import defaultdict

from distance.classes import DefaultClasses
from .base import ObjectFilter


class DowngradeInfo(object):

    def __init__(self):
        self.warnings = {}

    def add_if(self, obj, attr, cond):
        value = getattr(obj, attr)
        if cond(value):
            self.warnings[attr] = value
        return self


class AnimatorDowngrader(object):

    _tags_ = ['Animator']

    def apply(self, obj, sec, index):
        if sec.version > 10:
            frag = obj['Animator']
            frag.container.version = 10
            return (DowngradeInfo()
                    .add_if(frag, 'double_pivot_distance', lambda x: (x or 0.0) > 0.05))
        return False


class EventListenerDowngrader(object):

    _tags_ = ['EventListener']

    def apply(self, obj, sec, index):
        if sec.version > 1:
            frag = obj['EventListener']
            frag.container.version = 1
            return (DowngradeInfo()
                    .add_if(frag, 'delay', lambda x: (x or 0.0) > 0.05))
        return False


class DowngradeFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        super().add_args(parser)
        parser.add_argument(":debug", action='store_true')
        grp = parser.add_mutually_exclusive_group()
        grp.set_defaults(mode='safe')

    def __init__(self, args):
        super().__init__(args)
        downgraders = [AnimatorDowngrader(), EventListenerDowngrader()]
        by_key = defaultdict(list)
        for d in downgraders:
            for tag in d._tags_:
                key = DefaultClasses.fragments.get_base_key(tag)
                by_key[key].append((tag, d))
        self.downgraders_by_key = dict(by_key)
        self.debug = args.debug
        self.num_downgraded = 0
        self.warnings = []

    def downgrade_fragments(self, obj):
        i = 0
        for sec in obj.sections:
            downgraders = self.downgraders_by_key.get(sec.to_key(noversion=True), ())
            if downgraders:
                for tag, d in downgraders:
                    info = d.apply(obj, sec, i)
                    if info:
                        if info.warnings:
                            self.warnings.append((tag, info.warnings))
                        self.num_downgraded += 1
            i += 1
        return obj,

    def filter_any_object(self, obj, levels, **kw):
        if levels == 0:
            return obj,
        self.downgrade_fragments(obj)
        return self.filter_group(obj, levels - 1, **kw)

    def print_summary(self, p):
        p(f"Downgraded fragments: {self.num_downgraded}")
        if self.warnings:
            p(f"Fragment warnings: {len(self.warnings)}")
            with p.tree_children(len(self.warnings)):
                for tag, warnings in self.warnings:
                    p.tree_next_child()
                    p(f"Fragment {tag!r} warnings: {len(warnings)}")
                    with p.tree_children(len(warnings)):
                        for name, value in warnings.items():
                            p.tree_next_child()
                            p(f"{name}: {value!r}")

# vim:set sw=4 ts=8 sts=4 et:
