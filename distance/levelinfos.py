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
        self.tags = dbytes.read_string()
        self.unknown_2 = dbytes.read_n(8)
        self.author = dbytes.read_string()
        self.path = dbytes.read_string()
        self.unknown_3 = dbytes.read_n(24)

    @staticmethod
    def iter_all(dbytes):
        try:
            while True:
                yield Level(dbytes)
        except EOFError:
            pass


class LevelInfos(object):

    def __init__(self, dbytes, read_levels=True):
        magic = dbytes.read_fixed_number(4)
        if magic != 66666666:
            raise IOError(f"invalid magic: {magic}")
        self.unknown_1 = dbytes.read_n(8)
        type_ident = dbytes.read_string()
        if type_ident != "WorkshopLevelInfos":
            raise IOError(f"invalid bytes filetype: {type_ident!r}")
        self.unknown_2 = dbytes.read_n(65)
        if read_levels:
            self.read_levels()
        self.dbytes = dbytes

    def iter_levels(self):
        return Level.iter_all(self.dbytes)

    def read_levels(self):
        self.levels = list(Level.iter_all(self.dbytes))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
