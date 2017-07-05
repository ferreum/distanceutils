#!/usr/bin/python
# File:        profileprogress.py
# Description: profileprogress
# Created:     2017-07-05


from .bytes import (BytesModel, S_COLOR_RGBA,
                    SECTION_TYPE, SECTION_UNK_1, SECTION_UNK_2, SECTION_UNK_3)
from .common import format_duration
from .constants import Completion, Mode, TIMED_MODES


FTYPE_PROFILEPROGRESS = 'ProfileProgress'


def format_score(mode, score, comp):
    comp_str = Completion.to_name(comp)
    mode_str = Mode.to_name(mode)
    if mode in TIMED_MODES:
        type_str = "time"
        if score < 0:
            score_str = "None"
        else:
            score_str = format_duration(score)
    else:
        type_str = "score"
        if score < 0:
            score_str = "None"
        else:
            score_str = str(score)
    return f"{mode_str} {type_str}: {score_str} ({comp_str})"


class LevelProgress(BytesModel):

    level_path = None
    completion = ()
    scores = ()

    def parse(self, dbytes):
        self.level_path = dbytes.read_string()
        self.recoverable = True
        self.add_unknown(value=dbytes.read_string())
        self.add_unknown(1)

        self.require_equal(SECTION_UNK_1, 4)
        num_levels = dbytes.read_fixed_number(4)
        self.completion = completion = []
        for i in range(num_levels):
            completion.append(dbytes.read_fixed_number(4))

        self.require_equal(SECTION_UNK_1, 4)
        num_levels = dbytes.read_fixed_number(4)
        self.scores = scores = []
        for i in range(num_levels):
            scores.append(dbytes.read_fixed_number(4, signed=True))
        self.add_unknown(8)

    def _print_data(self, p):
        p(f"Level path: {self.level_path!r}")
        for mode, (score, comp) in enumerate(zip(self.scores, self.completion)):
            if comp != Completion.UNPLAYED:
                p(format_score(mode, score, comp))


class ProfileProgress(BytesModel):

    level_s2 = None
    num_levels = None

    def parse(self, dbytes):
        self.require_type(FTYPE_PROFILEPROGRESS)
        s3 = self.require_section(SECTION_UNK_3)
        dbytes.pos = s3.data_end
        s2 = self.require_section(SECTION_UNK_2)
        if s2.value_id == 0x6A:
            self.level_s2 = s2
            self.add_unknown(4)
            self.num_levels = dbytes.read_fixed_number(4)
            self.add_unknown(4)

    def iter_levels(self):
        s2 = self.level_s2
        data_end = s2.data_end
        self.dbytes.pos = s2.data_start + 20
        with self.dbytes.limit(data_end):
            num = self.num_levels
            if num:
                for res in LevelProgress.iter_maybe_partial(self.dbytes, max_pos=data_end):
                    yield res
                    if not res[1]:
                        break
                    num -= 1
                    if num <= 0:
                        break

    def _print_data(self, p):
        if self.level_s2:
            p(f"Level progress version: {self.level_s2.version}")
            p(f"Level count: {self.num_levels}")
            for level, sane, exc in self.iter_levels():
                p.print_data_of(level)
        else:
            p("No level progress")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
