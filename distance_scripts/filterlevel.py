"""Apply filters to a level or CustomObject."""


import os
import sys
import argparse

from distance.level import Level
from distance.levelobjects import Group
from distance.base import BaseObject
from distance.bytes import MAGIC_9
from distance.filter import getfilter
from distance.printing import PrintContext
from distance.prober import BytesProber


PROBER = BytesProber(baseclass=BaseObject)
PROBER.add_type('Group', Group)
PROBER.add_fragment(Level, MAGIC_9)


def filterlevel_getfilter(name):
    if name == 'file':
        return FileFilter
    return getfilter(name)


class FileFilter(object):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(":src", help="File containing the filter definitions.")
        parser.add_argument(":relative_to", help="Path that src is relative to (used internally).")

    def __init__(self, args):
        src = args.src
        relative_to = args.__dict__.pop('relative_to', None) or '.'
        if not src.startswith('/'):
            src = os.path.join(relative_to, src)
        abssrc = os.path.abspath(src)
        self.src = os.path.relpath(src)
        def create(l):
            defaults = dict(relative_to=os.path.dirname(abssrc), **args.__dict__)
            return create_filter(l, defaults)
        with open(abssrc, 'r') as f:
            self.filters = [(create(l), l) for l in map(str.strip, f)]
        self.aborted = False

    def apply(self, content):
        for f, l in self.filters:
            f.apply(content)
        if not f.post_filter(content):
            self.aborted = True
            return

    def post_filter(self, p):
        return not self.aborted

    def print_summary(self, p):
        p(f"File: {self.src!r}")
        p(f"Filters: {len(self.filters)}")
        with p.tree_children():
            for f, l in self.filters:
                p.tree_next_child()
                p(f"Filter: {l}")
                f.print_summary(p)


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

    return [":" + ''.join(token) for token in iter_tokens(s)]


def create_filter(option, defaults):
    name, sep, argstr = option.partition(':')
    cls = filterlevel_getfilter(name)

    parser = argparse.ArgumentParser(prog=name, prefix_chars=':',
                                     add_help=False)
    parser.add_argument(':help', action='help', default=argparse.SUPPRESS,
                        help='show this help message and exit')
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
                        help="Maximum recursion depth.")
    parser.add_argument("-o", "--of", "--objfilter", dest='objfilters',
                        action='append', default=[],
                        help="Specify a filter option.")
    parser.add_argument("--list", action='store_true',
                        help="Dump result listing.")
    parser.add_argument("IN", nargs='?',
                        help="Level .bytes filename.")
    parser.add_argument("OUT", nargs='?',
                        help="output .bytes filename.")
    args = parser.parse_args()

    defaults = dict(maxrecurse=args.maxrecurse)
    filters = [create_filter(f, defaults) for f in args.objfilters]

    if args.IN is None:
        print(f"{parser.prog}: No input file specified.", file=sys.stderr)
        return 1

    if args.OUT is None:
        print(f"{parser.prog}: No output file specified.", file=sys.stderr)
        return 1

    write_mode = 'xb'
    if args.force:
        write_mode = 'wb'
    elif os.path.exists(args.OUT):
        print(f"{parser.prog}: file {args.OUT} exists."
              " pass -f to force.", file=sys.stderr)
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
