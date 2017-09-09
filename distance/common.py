# File:        common.py
# Description: common
# Created:     2017-06-15


import os
import math


CACHE_PATH = os.path.expanduser('~/.cache/dst')

PROFILE_PATH = (os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
                + '/refract/Distance')


def get_cache_filename(filename):
    return os.path.join(CACHE_PATH, filename)


def get_profile_filename(filename):
    return os.path.join(PROFILE_PATH, filename)


def format_bytes(data, fmt='02x'):
    if isinstance(data, (tuple, list)):
        return ', '.join(format_bytes(d) for d in data)
    else:
        return ' '.join(format(b, fmt) for b in data)


def format_duration(msec):
    if msec is None:
        return "None"
    if math.isnan(msec):
        return "NaN"
    if not isinstance(msec, int):
        msec = int(msec)
    negative = msec < 0
    if negative:
        msec = -msec
    hours = ""
    if msec >= 3600000:
        hours = f"{msec // 3600000}:"
        msec = msec % 3600000
    mins = msec // 60000
    msec %= 60000
    sec = msec // 1000
    msec %= 1000
    return f"{'-' if negative else ''}{hours}{mins:02}:{sec:02}.{msec:03}"


def format_duration_dhms(msec):
    if msec is None:
        return "None"
    if math.isnan(msec):
        return "NaN"
    if not isinstance(msec, int):
        msec = int(msec)
    if msec == 0:
        return "0"
    result = []
    if msec < 0:
        msec = -msec
        result.append("-")
    for n, unit in ("d", 86400000), ("h", 3600000), ("m", 60000), ("s", 1000), ("ms", 1):
        v = msec // unit
        msec %= unit
        if v:
            result.append(f"{v}{n}")
    return ' '.join(result)


def format_distance(meters):
    if math.isnan(meters):
        return "NaN"
    km = int(meters) / 1000.0
    return f"{km} km"


def format_color(color):
    if color is None:
        return "None"
    return ', '.join(f"{round(c * 100)}%" for c in color)


def format_unknown_value(value):
    if isinstance(value, (bytes, bytearray)):
        return format_bytes(value)
    else:
        return repr(value)


def format_unknown(unknown):
    return ', '.join(format_unknown_value(v) for v in unknown)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
