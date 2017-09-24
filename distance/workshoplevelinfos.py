"""WorkshopLevelInfos .bytes support."""


from .bytes import BytesModel, MAGIC_2
from .base import BaseObject
from .printing import format_bytes
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
        self.id = dbytes.read_int(8)
        self.recoverable = True
        self.title = dbytes.read_str()
        self.description = dbytes.read_str()
        self.updated_date = dbytes.read_int(4)
        self.published_date = dbytes.read_int(4)
        self.tags = dbytes.read_str()
        self.authorid = dbytes.read_int(8)
        self.author = dbytes.read_str()
        self.path = dbytes.read_str()
        self.published_by_user = dbytes.read_byte()
        self._add_unknown(7)
        self.upvotes = dbytes.read_int(4)
        self.downvotes = dbytes.read_int(4)
        self._add_unknown(4)
        self.rating = dbytes.read_byte()
        self._add_unknown(3)


class WorkshopLevelInfos(BaseObject):

    num_levels = 0

    def _read(self, dbytes):
        self._require_type(FTYPE_WSLEVELINFOS)
        BaseObject._read(self, dbytes)

    def _read_section_data(self, dbytes, sec):
        if sec.match(MAGIC_2, 0x6d):
            self.levels_s2 = sec
            self.num_levels = dbytes.read_int(4)
            return False
        return BaseObject._read_section_data(self, dbytes, sec)

    def iter_levels(self):
        dbytes = self.dbytes
        if self.levels_s2:
            dbytes.pos = self.levels_s2.data_start + 20
            return Level.iter_n_maybe(dbytes, self.num_levels)
        else:
            return ()

    def _print_data(self, p):
        p(f"Levelinfos: {self.num_levels}")
        with p.tree_children():
            for level in self.iter_levels():
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
                if level.exception:
                    p.print_exception(level.exception)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
