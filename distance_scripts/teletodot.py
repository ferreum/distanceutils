"""Generate GraphViz DOT from teleporter connections in a level."""


import argparse

from distance import Level, DefaultClasses


SubTeleporter = DefaultClasses.level_subobjects.klass('Teleporter')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("FILE", help=".bytes filename")
    args = parser.parse_args()

    level = Level(args.FILE)

    def get_teleporters(gen):
        for obj in gen:
            teles = [o for o in obj.children
                     if o.has_any('TeleporterEntrance') or
                     o.has_any('TeleporterExit')]
            if teles:
                yield obj, teles
            if not obj.sane_end_pos:
                break
            if obj.is_object_group:
                yield from get_teleporters(obj.children)

    dests = {}
    srcs = {}
    sub_to_main = {}

    def add_to_listmap(listmap, key, value):
        try:
            l = listmap[key]
        except KeyError:
            listmap[key] = [value]
        else:
            l.append(value)

    for i, (obj, teles) in enumerate(
            get_teleporters(obj for l in level.layers
                            for obj in l.objects)):
        for tele in teles:
            sub_to_main[tele] = obj
            parts = [obj.type]
            try:
                exit = tele['TeleporterExit']
            except KeyError as e:
                if e.is_present:
                    parts.append("??")
            else:
                add_to_listmap(dests, exit.link_id, tele)
                parts.append(f"{tele.link_id}")
            try:
                entrance = tele['TeleporterEntrance']
            except KeyError as e:
                if e.is_present:
                    parts.append("to ??")
            else:
                add_to_listmap(srcs, entrance.destination, tele)
                parts.append(f"to {entrance.destination}")
            tele.__id = f"t{i}_{obj.type}"
            tele.__label = ' '.join(parts)

    import numpy as np

    print("digraph tele {")
    for l in srcs.values():
        for src in l:
            dest_list = dests.get(src.destination, ())
            print(f'  {src.__id} [label="{src.__label}"]')
            for dest in dest_list:
                dmain = sub_to_main[dest]
                smain = sub_to_main[src]
                dist = np.linalg.norm(
                    np.array(dmain.real_transform.effective()[0]) - np.array(smain.real_transform.effective()[0]))
                print(f'  {src.__id}->{dest.__id} [label="{dist:n} units"];')
    for dest_list in dests.values():
        for dest in dest_list:
            print(f'  {dest.__id} [label="{dest.__label}"];')
    print("}")

    return 0


if __name__ == '__main__':
    exit(main())


# vim:set sw=4 ts=8 sts=4 et:
