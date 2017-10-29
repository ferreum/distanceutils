"""Apply filters to a level or CustomObject."""


import os
import sys
import argparse

from distance.level import Level
from distance.levelobjects import Group
from distance.base import BaseObject
from distance.bytes import MAGIC_9
from distance.filter import (
    GoldifyFilter,
    RemoveFilter,
    UnkillFilter,
    VisualizeFilter,
    SettingsFilter,
)
from distance.printing import PrintContext
from distance.prober import BytesProber


PROBER = BytesProber()


PROBER.add_type('Group', Group)
PROBER.add_fragment(Level, MAGIC_9)

@PROBER.func
def _detect_other(section):
    return BaseObject


FILTERS = {}
FILTERS['goldify'] = GoldifyFilter
FILTERS['rm'] = RemoveFilter
FILTERS['unkill'] = UnkillFilter
FILTERS['vis'] = VisualizeFilter
FILTERS['settings'] = SettingsFilter


def make_arglist(s):

    def iter_tokens(source):
        if not source:
            return
        token = []
        escape = False
        for char in source:
            if escape:
                escape = False
                token.append(char)
            elif char == '\\':
                escape = True
            elif char == ':':
                yield token
                token = []
            else:
                token.append(char)
        yield token

    return ["--" + ''.join(token) for token in iter_tokens(s)]


def create_filter(option, defaults):
    name, sep, argstr = option.partition(':')
    cls = FILTERS[name]

    parser = argparse.ArgumentParser(prog=name)
    parser.set_defaults(**defaults)
    cls.add_args(parser)
    args = parser.parse_args(make_arglist(argstr))

    return cls(args)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("-f", "--force", action='store_true',
                        help="Allow overwriting OUT file.")
    parser.add_argument("-l", "--maxrecurse", type=int, default=-1,
                        help="Maximum of recursions. 0 only lists layer objects.")
    parser.add_argument("-o", "--of", "--objfilter", dest='objfilters',
                        action='append', default=[],
                        help="Specify a filter option.")
    parser.add_argument("--list", action='store_true',
                        help="Dump result listing.")
    parser.add_argument("IN",
                        help="Level .bytes filename.")
    parser.add_argument("OUT",
                        help="output .bytes filename.")
    args = parser.parse_args()

    defaults = dict(maxrecurse=args.maxrecurse)
    filters = [create_filter(f, defaults) for f in args.objfilters]

    write_mode = 'xb'
    if args.force:
        write_mode = 'wb'
    elif os.path.exists(args.OUT):
        print(f"file {args.OUT} exists. pass -f to force.", file=sys.stderr)
        return 1

    content = PROBER.read(args.IN)

    p = PrintContext(flags=('groups', 'subobjects'))

    for f in filters:
        f.apply(content)
        if not f.post_filter(content):
            return 1
        f.print_summary(p)

    if args.list:
        p.print_data_of(content)

    print("writing...")
    n = content.write(args.OUT, write_mode=write_mode)
    print(f"{n} bytes written")
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
