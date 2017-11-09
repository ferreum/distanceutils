"""WorkshopLevelInfos .bytes support."""


from .bytes import BytesModel, MAGIC_2
from .base import (
    BaseObject, Fragment,
    BASE_FRAG_PROBER,
    ForwardFragmentAttrs,
    require_type,
)
from .prober import BytesProber
from .constants import Rating


FTYPE_WSLEVELINFOS = "WorkshopLevelInfos"

FRAG_PROBER = BytesProber()

FRAG_PROBER.extend(BASE_FRAG_PROBER)


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
        self.id = dbytes.read_uint8()
        self.title = dbytes.read_str()
        self.description = dbytes.read_str()
        self.updated_date = dbytes.read_uint4()
        self.published_date = dbytes.read_uint4()
        self.tags = dbytes.read_str()
        self.authorid = dbytes.read_uint8()
        self.author = dbytes.read_str()
        self.path = dbytes.read_str()
        self.published_by_user = dbytes.read_byte()
        dbytes.read_bytes(7)
        self.upvotes = dbytes.read_uint4()
        self.downvotes = dbytes.read_uint4()
        dbytes.read_bytes(4)
        self.rating = dbytes.read_uint4()


@FRAG_PROBER.fragment(MAGIC_2, 0x6d, 0)
class WorkshopLevelInfosFragment(Fragment):

    levels = ()

    def _read_section_data(self, dbytes, sec):
        num_levels = dbytes.read_uint4()
        self.levels = Level.lazy_n_maybe(dbytes, num_levels,
                                         start_pos=sec.content_start + 8)


@ForwardFragmentAttrs(WorkshopLevelInfosFragment, levels=())
@require_type(FTYPE_WSLEVELINFOS)
class WorkshopLevelInfos(BaseObject):

    fragment_prober = FRAG_PROBER

    def _print_data(self, p):
        p(f"Levelinfos: {len(self.levels)}")
        with p.tree_children():
            for level in self.levels:
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
                if level.exception:
                    p.print_exception(level.exception)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
