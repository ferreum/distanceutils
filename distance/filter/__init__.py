

from distance.filter.goldify import GoldifyFilter
from distance.filter.remove import RemoveFilter
from distance.filter.unkill import UnkillFilter
from distance.filter.visualize import VisualizeFilter
from distance.filter.settings import SettingsFilter
from distance.filter.downgrade import DowngradeFilter


__all__ = [
    'getfilter',
]


_filters = {
    'goldify' : GoldifyFilter,
    'rm' : RemoveFilter,
    'unkill' : UnkillFilter,
    'vis' : VisualizeFilter,
    'settings' : SettingsFilter,
    'downgrade' : DowngradeFilter,
}


def getfilter(name):
    return _filters[name]


# vim:set sw=4 ts=8 sts=4 et:
