"""Common game constants, enums, flags."""


class FancyEnum(object):

    @classmethod
    def to_name(clazz, value, unk_fmt="Unknown(%s)"):
        try:
            return clazz.Names[value]
        except KeyError:
            return unk_fmt % (value,)


class Mode(FancyEnum):

    SPRINT = 1
    STUNT = 2
    SOCCER = 3
    FREE_ROAM = 4
    TAG = 5
    CHALLENGE = 8
    ADVENTURE = 9
    SPEED_AND_STYLE = 10
    TRACKMOGRIFY = 11
    MAIN_MENU = 13

    Names = {
        SPRINT: "Sprint",
        STUNT: "Stunt",
        SOCCER: "Soccer",
        FREE_ROAM: "Free Roam",
        TAG: "Reverse Tag",
        CHALLENGE: "Challenge",
        ADVENTURE: "Adventure",
        SPEED_AND_STYLE: "Speed and Style",
        TRACKMOGRIFY: "Trackmogrify",
        MAIN_MENU: "Main Menu",
    }


TIMED_MODES = {Mode.SPRINT, Mode.SPEED_AND_STYLE, Mode.CHALLENGE}


class Completion(FancyEnum):

    UNPLAYED = 0
    STARTED = 1
    COMPLETED = 2
    BRONZE = 3
    SILVER = 4
    GOLD = 5
    DIAMOND = 6

    Names = {
        UNPLAYED: "Unplayed",
        STARTED: "Did not finish",
        COMPLETED: "Completed",
        BRONZE: "Bronze",
        SILVER: "Silver",
        GOLD: "Gold",
        DIAMOND: "Diamond",
    }


class Difficulty(FancyEnum):

    CASUAL = 0
    NORMAL = 1
    ADVANCED = 2
    EXPERT = 3
    NIGHTMARE = 4
    NONE = 5

    Names = {
        0: "Casual",
        1: "Normal",
        2: "Advanced",
        3: "Expert",
        4: "Nightmare",
        5: "None",
    }


class AbilityToggle(FancyEnum):

    INF_COOLDOWN = 0
    NO_WINGS = 1
    NO_JUMP = 2
    NO_BOOST = 3
    NO_JETS = 4

    Names = {
        INF_COOLDOWN: "Infinite Cooldown",
        NO_WINGS: "Disable Flying",
        NO_JUMP: "Disable Jumping",
        NO_BOOST: "Disable Boosting",
        NO_JETS: "Disable Jet Rotation",
    }

    @classmethod
    def to_name_for_value(clazz, toggle, value):
        try:
            if value == 0 or value == 1:
                return clazz.Names[toggle]
        except KeyError:
            pass
        return f"Unknown({toggle}, {value})"


class Rating(FancyEnum):

    NONE = 0
    POSITIVE = 1
    NEGATIVE = 2

    Names = {
        NONE: "None",
        POSITIVE: "Positive",
        NEGATIVE: "Negative",
    }


class ForceType(FancyEnum):

    WIND = 0
    GRAVITY = 1

    Names = {
        WIND: "Wind",
        GRAVITY: "Gravity",
    }


LAYER_FLAG_NAMES = ({0: "", 1: "Active"},
                    {0: "", 1: "Frozen"},
                    {0: "Invisible", 1: ""})


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
