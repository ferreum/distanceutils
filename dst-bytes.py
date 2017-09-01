#!/usr/bin/python
# File:        dst-bytes.py
# Description: dst-bytes
# Created:     2017-06-28


import sys
import argparse

from distance.bytes import DstBytes, PrintContext
from distance.knowntypes import maybe_partial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", nargs='+', help=".bytes filename")
    parser.add_argument("--unknown", action='append_const', const='unknown', dest='flags',
                        help="Print unknown data too (same as -f unknown).")
    parser.add_argument("-f", "--flags", action='append',
                        help="Add flags.")
    parser.set_defaults(flags=[])
    args = parser.parse_args()

    flags = [flag.strip() for arg in args.flags for flag in arg.split(',')]

    if not 'nogroups' in flags or 'nogroup' in flags:
        flags.append('groups')
    if not 'nosubobjects' in flags or 'nosubobject' in flags:
        flags.append('subobjects')

    p = PrintContext(file=sys.stdout, flags=flags)

    have_error = False
    for fname in args.FILE:
        with open(fname, 'rb') as f:
            try:
                if len(args.FILE) > 1:
                    p("")
                    p(f"File: {f.name!r}")
                obj, _, exception = maybe_partial(DstBytes(f))
                p.print_data_of(obj)
            except Exception as e:
                p.print_exception(e)
                have_error = True
    return 1 if have_error else 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
