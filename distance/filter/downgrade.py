"""Filter for downgrading objects"""


from collections import defaultdict

from distance._default_classes import DefaultClasses
from .base import ObjectFilter


class AnimatorDowngrader(object):

    _tags_ = ['Animator']

    def apply(self, obj, sec, index):
        if sec.version > 10:
            obj['Animator'].container.version = 10
            return True
        return False


class EventListenerDowngrader(object):

    _tags_ = ['EventListener']

    def apply(self, obj, sec, index):
        if sec.version > 1:
            obj['EventListener'].container.version = 1
            return True
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
                by_key[key].append(d)
        self.downgraders_by_key = dict(by_key)
        self.debug = args.debug
        self.num_downgraded = 0

    def downgrade_fragments(self, obj):
        i = 0
        for sec in obj.sections:
            downgraders = self.downgraders_by_key.get(sec.to_key(noversion=True), ())
            if downgraders:
                for d in downgraders:
                    if d.apply(obj, sec, i):
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

# vim:set sw=4 ts=8 sts=4 et:
