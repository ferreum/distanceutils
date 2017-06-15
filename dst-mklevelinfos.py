#!/usr/bin/python
# File:        dst-mklevelinfos.py
# Description: dst-mklevelinfos
# Created:     2017-06-25


import argparse
import re
import sqlite3

from distance.levelinfos import LevelInfos
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
        c.execute("""CREATE TABLE IF NOT EXISTS level(
                  id, title, description, tags, author, authorid, path)""")
        c.execute("CREATE INDEX IF NOT EXISTS lvl_id_path ON level(id, path)")
        c.execute("CREATE INDEX IF NOT EXISTS lvl_path ON level(path)")
        c.execute("CREATE INDEX IF NOT EXISTS lvl_author ON level(author)")

        c.execute("DELETE FROM level")

        dbytes = DstBytes(args.FILE)
        infos = LevelInfos(dbytes, read_levels=False)
        count = 0
        for level in infos.iter_levels():
            values = [level.id, level.title, level.description, level.tags, level.author]
            path = level.path
            match = re.search(r"WorkshopLevels/+([0-9]+)/+", path)
            if match:
                values.append(int(match.group(1)))
            else:
                values.append(None)
            values.append(path)
            c.execute("""INSERT INTO level
                      (id, title, description, tags, author, authorid, path)
                      VALUES (?, ?, ?, ?, ?, ?, ?)""", values)
            count += 1

        conn.commit()
        print(f"found {count} levels")
    finally:
        c.close()
    return 0


if __name__ == '__main__':
    import sys
    exit(main(sys.argv))

# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
