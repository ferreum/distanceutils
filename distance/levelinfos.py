#!/usr/bin/python
# File:        levelinfos.py
# Description: levelinfos
# Created:     2017-06-24


class Level(object):

    def __init__(self, dbytes):
        self.id = dbytes.read_fixed_number(8)
        self.title = dbytes.read_string()
        self.description = dbytes.read_string()
        self.unknown_1 = dbytes.read_n(8)
        self.flags = dbytes.read_string()
        self.unknown_2 = dbytes.read_n(8)
        self.author = dbytes.read_string()
        self.path = dbytes.read_string()
        self.unknown_3 = dbytes.read_n(24)

    @staticmethod
    def read_all(dbytes):
        levels = []
        try:
            while True:
                levels.append(Level(dbytes))
        except EOFError:
            return levels


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
