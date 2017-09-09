#!/usr/bin/python
# File:        mklevelinfos.py
# Description: Creates WorkshopLevelInfos cache database
# Created:     2017-06-25


import argparse
import sqlite3

from distance.workshoplevelinfos import WorkshopLevelInfos
from distance.bytes import DstBytes
from distance.common import get_cache_filename, get_profile_filename


def main():
    parser = argparse.ArgumentParser(
        description="Creates WorkshopLevelInfos cache database.")
    parser.add_argument("--db", help="database filename.")
    parser.add_argument("FILE", nargs='?',
                        help="WorkshopLevelInfos.bytes filename.")
    args = parser.parse_args()

    if args.db is None:
        args.db = get_cache_filename("data.db")
    if args.FILE is None:
        args.FILE = get_profile_filename(
            "Levels/WorkshopLevels/WorkshopLevelInfos.bytes")

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

        with open(args.FILE, 'rb') as infos_file:
            dbytes = DstBytes(infos_file)
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
    exit(main())

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0: