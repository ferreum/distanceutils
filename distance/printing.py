"""Utilities for printing object data."""


import sys
import traceback
import math
from contextlib import contextmanager


class PrintContext(object):

    """Context class for printing objects."""

    def __init__(self, file=sys.stdout, flags=()):
        self.file = file
        self.flags = flags
        # buffered lines, object finished
        self._tree_data = [], []

    @classmethod
    def for_test(clazz, file=None, flags=None):
        if flags is None:
            class ContainsEverything:
                def __contains__(self, obj):
                    return True
            flags = ContainsEverything()
        p = PrintContext(file=file, flags=flags)
        def print_exc(e):
            raise e
        p.print_exception = print_exc
        return p

    def __call__(self, text):
        buf, ended = self._tree_data
        if buf:
            last = buf[-1]
            if ended[-1]:
                self.tree_push_up(last, False)
                last.clear()
            last.extend(text.split('\n'))
        else:
            f = self.file
            if f is not None:
                print(text, file=f)

    def tree_push_up(self, lines, last):
        if not lines:
            return
        buf, ended = self._tree_data
        ended[-1] = False
        if len(buf) > 1:
            dest = buf[-2]
            push_line = dest.append
        else:
            f = self.file
            def push_line(line):
                if f is not None:
                    print(line, file=f)
        it = iter(lines)
        if last:
            prefix = "└─ "
        else:
            prefix = "├─ "
        push_line(prefix + next(it))
        if last:
            prefix = "   "
        else:
            prefix = "│  "
        for line in it:
            push_line(prefix + line)

    @contextmanager
    def tree_children(self):
        buf, ended = self._tree_data
        lines = []
        buf.append(lines)
        ended.append(False)
        try:
            yield
        finally:
            self.tree_push_up(lines, True)
            buf.pop()
            ended.pop()

    def tree_next_child(self):
        buf, ended = self._tree_data
        if buf and buf[-1]:
            ended[-1] = True

    def print_data_of(self, obj):
        obj.print_data(p=self)

    def print_exception(self, exc):
        exc_str = traceback.format_exception(type(exc), exc, exc.__traceback__)
        for part in exc_str:
            if part.endswith('\n'):
                part = part[:-1]
            for line in part.split('\n'):
                self(line)
        try:
            self(f"Exception start: 0x{exc.start_pos:08x}")
            self(f"Exception pos:   0x{exc.exc_pos:08x}")
        except AttributeError:
            pass


class Counters(object):

    num_objects = 0
    num_layers = 0
    layer_objects = 0
    grouped_objects = 0

    def print_data(self, p):
        if self.num_layers:
            p(f"Total layers: {self.num_layers}")
        if self.layer_objects:
            p(f"Total objects in layers: {self.layer_objects}")
        if self.grouped_objects and self.grouped_objects != self.num_objects:
            p(f"Total objects in groups: {self.grouped_objects}")
        if self.num_objects != self.layer_objects or self.num_objects == 0:
            p(f"Total objects: {self.num_objects}")


@contextmanager
def need_counters(p):
    try:
        p.counters
    except AttributeError:
        pass
    else:
        yield None
        return
    c = Counters()
    p.counters = c
    yield c
    del p.counters


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


def format_transform(trans):
    if trans is None:
        return 'None'
    def format_floats(floats):
        return ', '.join(format(f, '.3f') for f in floats)
    return ', '.join(f"({format_floats(f)})" for f in trans)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
