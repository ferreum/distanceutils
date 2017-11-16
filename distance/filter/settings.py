"""Filter for modifying level settings"""


from collections import OrderedDict

from distance.level import Level
from distance.filter.base import ObjectFilter
from distance.constants import AbilityToggle as Ability, Mode


MODE_NAMES = {
    'sprint': Mode.SPRINT,
    'stunt': Mode.STUNT,
    'soccer': Mode.SOCCER,
    'freeroam': Mode.FREE_ROAM,
    'tag': Mode.TAG,
    'challenge': Mode.CHALLENGE,
    'adventure': Mode.ADVENTURE,
    'speedstyle': Mode.SPEED_AND_STYLE,
    'sns': Mode.SPEED_AND_STYLE,
    'trackmogrify': Mode.TRACKMOGRIFY,
    'mogrify': Mode.TRACKMOGRIFY,
    'trackmog': Mode.TRACKMOGRIFY,
    'mainmenu': Mode.MAIN_MENU,
    'menu': Mode.MAIN_MENU,
}


ABILITY_NAMES = {
    'heat': Ability.INF_COOLDOWN,
    'wings': Ability.NO_WINGS,
    'fly': Ability.NO_WINGS,
    'jump': Ability.NO_JUMP,
    'boost': Ability.NO_BOOST,
    'jets': Ability.NO_JETS,
}


ABILITIES_GOD = [0, 0, 0, 0, 0]
ABILITIES_GOD[Ability.INF_COOLDOWN] = 1


def get_all_modes():
    result = OrderedDict()
    for mode in sorted(MODE_NAMES.values()):
        result[mode] = 1
    return result


def parse_modes(arg):
    result = OrderedDict()
    for a in arg.split(","):
        a = a.lower()
        if a == 'all':
            return get_all_modes()
        if a == 'none':
            return {}
        mode = MODE_NAMES[a]
        result[mode] = 1
    return result


def parse_abilities(arg):
    result = [1] * 5
    for s in arg.split(","):
        s = s.lower()
        if s == 'all':
            return (0,) * 5
        if s == 'god':
            return tuple(ABILITIES_GOD)
        if s == 'none':
            return (1,) * 5
        ability = ABILITY_NAMES[s]
        result[ability] = 0
    return tuple(result)


class SettingsFilter(ObjectFilter):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(":name", help="Set the level name.")
        parser.add_argument(":namefmt", default='{name}',
                            help="Specify level name by format.")
        parser.add_argument(":modes", type=parse_modes,
                            help="Set game modes.")
        parser.add_argument(":modes+", type=parse_modes, dest='modes_add',
                            default=(),
                            help="Add game modes.")
        parser.add_argument(":modes-", type=parse_modes, dest='modes_remove',
                            default=(),
                            help="Remove game modes.")
        parser.add_argument(":abilities", type=parse_abilities,
                            help="Set enabled abilities.")

    def __init__(self, args):
        args.maxrecurse = 0
        super().__init__(args)
        self.name = args.name
        self.namefmt = args.namefmt
        self.modes = args.modes
        self.modes_add = args.modes_add
        self.modes_remove = args.modes_remove
        self.abilities = args.abilities
        self.applied_version = None

    def apply(self, content):
        if not isinstance(content, Level):
            raise ValueError("settings filter can only "
                             "be used with Levels.")
        settings = content.settings

        name = settings.name
        if self.name is not None:
            name = self.name
        name = self.namefmt.format(
            name,
            name = name,
            version = settings.version,
        )
        settings.name = name
        content.name = name

        modes = OrderedDict(settings.modes)
        if self.modes is not None:
            modes = OrderedDict(self.modes)
        for mode in self.modes_add:
            modes[mode] = 1
        for mode in self.modes_remove:
            modes[mode] = 0
        settings.modes = modes

        if self.abilities is not None:
            settings.abilities = self.abilities

        self.applied_version = settings.version

        return content

    def print_summary(self, p):
        if self.applied_version is not None:
            p(f"Settings applied (version {self.applied_version})")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
