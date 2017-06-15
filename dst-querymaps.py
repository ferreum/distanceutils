#!/usr/bin/python
# File:        dst-querymaps.py
# Description: dst-querymaps
# Created:     2017-06-15

import sys
import argparse
import sqlite3
import re

from distance.common import get_cache_filename

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="map database filename.")
    parser.add_argument("--stdin-paths", action='store_true',
                        help="filter by path read from stdin.")
    parser.add_argument("--ids", action='store_true',
                        help="print IDs of matching levels.")
    parser.add_argument("--where", nargs='*', metavar=('COND', 'ARG'),
                        help="specify WHERE clause.")
    parser.add_argument("--order-by", help="specify ORDER BY clause.")
    args = parser.parse_args(argv[1:])

    if not args.db:
        args.db = get_cache_filename('data.db')

    cond_parts = []
    params = []

    if args.where:
        cond_parts += args.where[0]
        params.extend(args.where[1:])

    if args.stdin_paths:
        if cond_parts:
            cond_parts += " AND "
        cond_parts += "map.name IN ("
        for i, line in enumerate(sys.stdin):
            params += re.sub(r"\\\\", r"\\", re.sub(r"\\n", r"\n", line))
            cond_parts += "?" if i == 0 else ", ?"
        cond_parts += ")"

    if not cond_parts:
        cond_parts += "1"

    if args.ids:
        fields = "id"
    else:
        fields = "title, path"
    query = f"SELECT {fields} FROM level"
    if cond_parts:
        query += " WHERE " + ''.join(cond_parts)
    if args.order_by:
        query += " ORDER BY " + args.order_by

    conn = sqlite3.connect(args.db)
    try:
        found = False
        if args.ids:
            for row in conn.execute(query, params):
                sys.stdout.write(f"{row[0]}\n")
                found = True
        else:
            for row in conn.execute(query, params):
                sys.stdout.write(re.sub(r"\s", " ", row[0]))
                sys.stdout.write("\t")
                sys.stdout.write(re.sub(r"\n", r"\\n", re.sub(r"\\", r"\\\\", row[1])))
                sys.stdout.write("\n")
                found = True
    finally:
        conn.close()
    return 0 if found else 1


if __name__ == '__main__':
    try:
        exit(main(sys.argv))
    except BrokenPipeError:
        exit(1)

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
