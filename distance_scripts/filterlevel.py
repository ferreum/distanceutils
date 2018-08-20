"""Apply filters to a level or CustomObject."""


import os
import sys
import argparse
from contextlib import contextmanager

from distance import DefaultClasses
from distance.levelobjects import LevelObject
from distance.filter import getfilter
from distance.printing import PrintContext


level_objects = DefaultClasses.level_objects


def filterlevel_getfilter(name):
    if name == 'file':
        return FileFilter
    return getfilter(name)


@contextmanager
def optcontext(obj, func, *args, **kw):
    if obj is None:
        yield
    else:
        with getattr(obj, func)(*args, **kw) as o:
            yield o


def apply_filters(filters, content, p=None, **kw):
    if p:
        p(f"Filters: {len(filters)}")
    with optcontext(p, 'tree_children', count=len(filters)):
        for f in filters:
            if p:
                p.tree_next_child()
                p(f"Filter: {f.__def_string}")
            if not f.apply(content, p=p, **kw):
                return False
    return True


class FileFilter(object):

    @classmethod
    def add_args(cls, parser):
        parser.add_argument(":src", help="File containing the filter definitions.")
        parser.add_argument(":relative_to", help="Path that src is relative to (used internally).")
        parser.description = "Load a filter chain from file."
        parser.epilog = """
        Filter files consist any number of filters, one per line.
        Filters are formatted as per the -o/--of/--objfilter argument.
        Empty lines and lines starting with '#' are ignored.
        """

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
            self.filters = [create(l) for l in map(str.strip, f)
                            if l and not l.startswith('#')]
        self.aborted = False

    def apply(self, content, p=None, **kw):
        if p:
            p(f"File: {self.src!r}")
            apply_filters(self.filters, content, p=p)
        return True


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

    flt = cls(args)
    flt.__def_string = option
    return flt


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
    elif args.OUT != '-' and os.path.exists(args.OUT):
        print(f"{parser.prog}: file {args.OUT} exists."
              " pass -f to force.", file=sys.stderr)
        return 1

    if args.IN == '-':
        from io import BytesIO
        srcarg = BytesIO(sys.stdin.buffer.read())
    else:
        srcarg = args.IN
    content = DefaultClasses.level_like.read(srcarg)

    is_wrapped = False
    if isinstance(content, LevelObject) and content.type != 'Group':
        is_wrapped = True
        content = DefaultClasses.level_objects.create('Group', children=[content])

    p = PrintContext(file=sys.stderr, flags=('groups', 'subobjects'))

    if not apply_filters(filters, content, p=p):
        return 1

    if is_wrapped and len(content.children) == 1:
        content = content.children[0]

    if args.list:
        p.print_object(content)

    print("writing...", file=sys.stderr)
    if args.OUT == '-':
        destarg = sys.stdout.buffer
    else:
        destarg = args.OUT
    n = content.write(destarg, write_mode=write_mode)
    print(f"{n} bytes written", file=sys.stderr)
    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et:
