#!/usr/bin/python
# File:        dst-mklevelinfos.py
# Description: dst-mklevelinfos
# Created:     2017-06-25


import argparse
import re
import sqlite3
from datetime import datetime

from distance.workshoplevelinfos import WorkshopLevelInfos
from distance.bytes import DstBytes
from distance.common import get_cache_filename


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="database filename.")
    parser.add_argument("FILE", type=argparse.FileType('rb'),
                        help="WorkshopLevelInfos.bytes filename.")
    args = parser.parse_args(argv[1:])

    if args.db is None:
        args.db = get_cache_filename("data.db")

    conn = sqlite3.connect(args.db)

    c = conn.cursor()
    try:
        c.execute("DROP TABLE level")
        c.execute("""CREATE TABLE level(
                  id, title, description, updated_date, published_date, tags,
                  author, authorid, path, published_by_user, upvotes, downvotes,
                  rating, unknown)""")
        c.execute("CREATE INDEX lvl_id_path ON level(id, path)")
        c.execute("CREATE INDEX lvl_path ON level(path)")
        c.execute("CREATE INDEX lvl_author ON level(author)")

        dbytes = DstBytes(args.FILE)
        infos = WorkshopLevelInfos(dbytes)
        count = 0
        for level, sane, exc in infos.iter_levels():
            values = [level.id, level.title, level.description, level.updated_date,
                      level.published_date, level.tags, level.author, level.authorid,
                      level.path, level.published_by_user, level.upvotes,
                      level.downvotes, level.rating]
            values.append(b''.join(level.unknown))
            c.execute("""INSERT INTO level
                      (id, title, description, updated_date, published_date,
                      tags, author, authorid, path, published_by_user, upvotes, downvotes,
                      rating, unknown)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values)
            count += 1
            if not sane:
                break

        conn.commit()
        print(f"found {count} levels")
    finally:
        c.close()
    return 0


if __name__ == '__main__':
    import sys
    exit(main(sys.argv))

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
