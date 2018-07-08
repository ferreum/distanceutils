"""WorkshopLevelInfos .bytes support."""


from construct import (
    Struct, Default, Rebuild, Byte, Bytes,
    this, len_,
)

from .bytes import Magic, Section
from .base import (
    BaseObject,
    fragment_attrs,
    require_type,
)
from .construct import (
    BaseConstructFragment,
    UInt, ULong, DstString
)
from .constants import Rating
from .prober import BytesProber


FTYPE_WSLEVELINFOS = "WorkshopLevelInfos"


class Probers(object):
    fragments = BytesProber()
    file = BytesProber()


def format_date(date):
    from datetime import datetime
    if date is None:
        return "None"
    return str(datetime.fromtimestamp(date))


@Probers.fragments.fragment
class WorkshopLevelInfosFragment(BaseConstructFragment):

    default_container = Section(Magic[2], 0x6d, 0)

    is_interesting = True

    _construct = Struct(
        'num_entries' / Rebuild(UInt, len_(this.levels)),
        'unk_0' / UInt, # entry version?
        'levels' / Default(Struct(
            'id' / ULong,
            'title' / DstString,
            'description' / DstString,
            'updated_date' / UInt,
            'published_date' / UInt,
            'tags' / DstString,
            'authorid' / ULong,
            'author' / DstString,
            'path' / DstString,
            'published_by_user' / Byte,
            'unk_0' / Bytes(7),
            'upvotes' / UInt,
            'downvotes' / UInt,
            'unk_1' / Bytes(4),
            'rating' / UInt,
        )[this.num_entries], ()),
    )

    def _print_data(self, p):
        super()._print_data(p)
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


@Probers.file.for_type
@fragment_attrs(WorkshopLevelInfosFragment, **WorkshopLevelInfosFragment._fields_map)
@require_type
class WorkshopLevelInfos(BaseObject):

    type = FTYPE_WSLEVELINFOS


# vim:set sw=4 ts=8 sts=4 et:
