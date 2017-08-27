#!/usr/bin/python
# File:        workshoplevelinfos.py
# Description: workshoplevelinfos
# Created:     2017-06-24


from .bytes import BytesModel, SECTION_UNK_2
from .common import format_bytes
from .constants import Rating


FTYPE_WSLEVELINFOS = "WorkshopLevelInfos"


def format_date(date):
    from datetime import datetime
    if date is None:
        return "None"
    return str(datetime.fromtimestamp(date))


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

    def _read(self, dbytes):
        self.id = dbytes.read_num(8)
        self.recoverable = True
        self.title = dbytes.read_string()
        self.description = dbytes.read_string()
        self.updated_date = dbytes.read_num(4)
        self.published_date = dbytes.read_num(4)
        self.tags = dbytes.read_string()
        self.authorid = dbytes.read_num(8)
        self.author = dbytes.read_string()
        self.path = dbytes.read_string()
        self.published_by_user = dbytes.read_byte()
        self.add_unknown(7)
        self.upvotes = dbytes.read_num(4)
        self.downvotes = dbytes.read_num(4)
        self.add_unknown(4)
        self.rating = dbytes.read_byte()
        self.add_unknown(3)


class WorkshopLevelInfos(BytesModel):

    num_levels = 0

    def _read(self, dbytes):
        ts = self.require_type(FTYPE_WSLEVELINFOS)
        self.report_end_pos(ts.data_end)
        self._read_sections(ts.data_end)

    def _read_section_data(self, dbytes, sec):
        if sec.ident == SECTION_UNK_2:
            if sec.value_id == 0x6d:
                self.levels_s2 = sec
                self.num_levels = dbytes.read_num(4)
                return True
        return BytesModel._read_section_data(self, dbytes, sec)

    def iter_levels(self):
        dbytes = self.dbytes
        if self.levels_s2:
            dbytes.pos = self.levels_s2.data_start + 20
            return Level.iter_maybe_partial(dbytes)
        else:
            return ()

    def _print_data(self, p):
        unk_str = ""
        p(f"Levelinfos: {self.num_levels}")
        with p.tree_children(0):
            for level, sane, exc in self.iter_levels():
                p.tree_next_child()
                p(f"Title: {level.title!r} ({level.id})")
                p(f"Author: {level.author!r} ({level.authorid})")
                if level.published_by_user:
                    p(f"Published by this steam user")
                p(f"Publish date: {format_date(level.published_date)}")
                p(f"Updated date: {format_date(level.updated_date)}")
                p(f"Tags: {level.tags!r}")
                p(f"Path: {level.path!r}")
                percent = "0"
                if level.upvotes:
                    percent = round(100 * level.upvotes / (level.upvotes + level.downvotes))
                p(f"Votes: {level.upvotes} up / {level.downvotes} down ({percent}%)")
                if 'description' in p.flags:
                    p(f"Description: {level.description}")
                if level.rating is not None and level.rating != Rating.NONE:
                    p(f"Rating: {Rating.to_name(level.rating)}")
                if 'unknown' in p.flags:
                    p(f"Unknown: {format_bytes(level.unknown)}")
                if exc:
                    p.print_exception(exc)
                if not sane:
                    break


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
