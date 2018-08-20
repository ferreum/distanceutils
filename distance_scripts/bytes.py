"""Dump data found in .bytes files."""


import sys
import argparse
from io import BytesIO

from distance.base import Fragment
from distance.printing import PrintContext
from distance.classes import CompositeProber
from distance import DefaultClasses
from ._common import handle_pipeerror


@handle_pipeerror
def main():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument("FILE", nargs='+', help=".bytes filename")
    parser.add_argument("-f", "--flags", action='append',
                        help="Add flags.")
    parser.set_defaults(flags=[])
    args = parser.parse_args()

    flags = [flag.strip() for arg in args.flags for flag in arg.split(',')]

    if not 'nogroups' in flags or 'nogroup' in flags:
        flags.append('groups')
    if not 'nosubobjects' in flags or 'nosubobject' in flags:
        flags.append('subobjects')
    if not 'nofragments' in flags or 'nofragment' in flags:
        flags.append('fragments')
    if 'offsets' in flags:
        flags.append('offset')
    if 'section' in flags:
        flags.append('sections')

    print_filename = 'filename' in flags or len(args.FILE) > 1

    prober = CompositeProber(
        probers=[DefaultClasses.fragments,
                 DefaultClasses.file],
        baseclass=Fragment,
    )

    p = PrintContext(flags=flags)

    have_error = False
    for fname in args.FILE:
        try:
            if print_filename:
                p("")
                p(f"File: {fname!r}")
            if fname == '-':
                srcarg = BytesIO(sys.stdin.buffer.read())
            else:
                srcarg = fname
            obj = prober.maybe(srcarg)
            p.print_object(obj)
        except BrokenPipeError:
            raise
        except Exception as e:
            p.print_exception(e)
            have_error = True
    return 1 if have_error else 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et:
