#!/usr/bin/python
# File:        levelinfos.py
# Description: levelinfos
# Created:     2017-06-24


from .bytes import BytesModel, SECTION_TYPE, SECTION_UNK_2
from .common import format_bytes


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
        self.require_type(FTYPE_LEVELINFOS)
        self.version = self.require_section(SECTION_UNK_2).version
        self.add_unknown(12)

    def iter_levels(self):
        return Level.iter_all(self.dbytes)

    def read_levels(self):
        self.levels = list(Level.iter_all(self.dbytes))

    def print_data(self, file, unknown=False):
        BytesModel.print_data(self, file, unknown=unknown)
        def p(*args):
            print(*args, file=file)
        unk_str = ""
        for level in self.iter_levels():
            if unknown:
                unk_str = f"Unknown: {format_bytes(level.unknown)} "
            if level.rating == RATING_POSITIVE:
                rate_str = " Rating: +"
            elif level.rating == RATING_NEGATIVE:
                rate_str = " Rating: -"
            elif level.rating == RATING_NONE:
                rate_str = ""
            else:
                rate_str = " Rating: Unknown ({level.rating})"
            p(f"Level: {unk_str}ID: {level.id} {level.title!r} by {level.author!r}({level.authorid}){rate_str}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
