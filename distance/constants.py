#!/usr/bin/python
# File:        constants.py
# Description: constants
# Created:     2017-07-05


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
    FREE_ROAM = 4
    TAG = 5
    CHALLENGE = 8
    ADVENTURE = 9
    SPEED_AND_STYLE = 10
    MAIN_MENU = 13

    Names = {
        SPRINT: "Sprint",
        STUNT: "Stunt",
        FREE_ROAM: "Free Roam",
        TAG: "Reverse Tag",
        CHALLENGE: "Challenge",
        ADVENTURE: "Adventure",
        SPEED_AND_STYLE: "Speed and Style",
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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
