#!/usr/bin/python
# File:        workshoplevelinfos.py
# Description: workshoplevelinfos
# Created:     2017-06-24


from .bytes import BytesModel, SECTION_UNK_2
from .common import format_bytes
from .constants import Rating


FTYPE_WSLEVELINFOS = "WorkshopLevelInfos"


class Level(BytesModel):

    id = None
    title = None
    description = None
    updated_date = None
    published_date = None
    tags = None
    authorid = None
    author = None
    path = None
    published_by_user = None
    upvotes = None
    downvotes = None
    rating = None

    def parse(self, dbytes):
        self.id = dbytes.read_fixed_number(8)
        self.recoverable = True
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


class WorkshopLevelInfos(BytesModel):

    def parse(self, dbytes):
        self.require_type(FTYPE_WSLEVELINFOS)
        self.version = self.require_section(SECTION_UNK_2).version
        self.add_unknown(12)

    def iter_levels(self):
        return Level.iter_maybe_partial(self.dbytes)

    def _print_data(self, p):
        unk_str = ""
        try:
            for level, sane, exc in self.iter_levels():
                if 'unknown' in p.flags:
                    unk_str = f"Unknown: {format_bytes(level.unknown)} "
                if level.rating is None:
                    rate_str = " Rating: None"
                elif level.rating == Rating.NONE:
                    rate_str = ""
                else:
                    rate_str = " Rating: " + Rating.to_name(level.rating)
                p(f"Level: {unk_str}ID: {level.id} {level.title!r} by {level.author!r}({level.authorid}){rate_str}")
                if exc:
                    p.print_exception(exc)
                if not sane:
                    break
        except Exception as e:
            p.print_exception(e)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0: