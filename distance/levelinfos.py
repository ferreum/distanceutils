#!/usr/bin/python
# File:        levelinfos.py
# Description: levelinfos
# Created:     2017-06-24


from .bytes import BytesModel, SECTION_TYPE, SECTION_UNK_2


RATING_NONE = 0
RATING_POSITIVE = 1
RATING_NEGATIVE = 2

FTYPE_LEVELINFOS = "WorkshopLevelInfos"


class Level(BytesModel):

    def parse(self, dbytes):
        self.unknown = unknown = []
        self.id = dbytes.read_fixed_number(8)
        self.title = dbytes.read_string()
        self.description = dbytes.read_string()
        self.updated_date = dbytes.read_fixed_number(4)
        self.published_date = dbytes.read_fixed_number(4)
        self.tags = dbytes.read_string()
        self.authorid = dbytes.read_fixed_number(8)
        self.author = dbytes.read_string()
        self.path = dbytes.read_string()
        self.published_by_user = dbytes.read_byte()
        self.add_unknown(7)
        self.upvotes = dbytes.read_fixed_number(4)
        self.downvotes = dbytes.read_fixed_number(4)
        self.add_unknown(4)
        self.rating = dbytes.read_byte()
        self.add_unknown(3)

    @staticmethod
    def iter_all(dbytes):
        try:
            while True:
                yield Level(dbytes)
        except EOFError:
            pass


class LevelInfos(BytesModel):

    def parse(self, dbytes):
        sections = self.read_sections_to(SECTION_UNK_2)
        ts = sections.get(SECTION_TYPE, ())
        if not ts:
            raise IOError("Missing type information")
        if ts[0].filetype != FTYPE_LEVELINFOS:
            raise IOError("Invalid bytes filetype: {ts.filetype!r}")
        self.add_unknown(12)

    def iter_levels(self):
        return Level.iter_all(self.dbytes)

    def read_levels(self):
        self.levels = list(Level.iter_all(self.dbytes))


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
