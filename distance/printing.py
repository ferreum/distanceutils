"""Utilities for printing object data."""


import sys
import traceback
import math
from itertools import islice
from contextlib import contextmanager


class PrintContext(object):

    """Context class for printing objects."""

    def __init__(self, file=sys.stdout, flags=()):
        self.file = file
        self.flags = flags
        # Data for each level of tree_children():
        # 0. Buffered lines for that level.
        # 1. Whether the child on that level has been ended
        #    by a call to tree_next_child().
        # 2. Counter of remaining children if 'count' was passed to
        #    tree_children() on that level.
        self._tree_data = [], [], []

    @classmethod
    def for_test(cls, file=None, flags=None):
        if flags is None:
            class ContainsEverything:
                def __contains__(self, obj):
                    return True
            flags = ContainsEverything()
        p = cls(file=file, flags=flags)
        def print_exc(e):
            raise e
        p.print_exception = print_exc
        return p

    def __call__(self, text):
        buf, ended, remain = self._tree_data
        if buf:
            count = remain[-1]
            if count is not None:
                self._tree_push_up(len(buf) - 1, [text], count <= 1)
            else:
                lines = buf[-1]
                if ended[-1]:
                    self._tree_push_up(len(buf) - 1, lines, False)
                    lines.clear()
                lines.extend(text.split('\n'))
        else:
            f = self.file
            if f is not None:
                print(text, file=f)

    def _tree_push_up(self, level, lines, last):
        while True:
            if not lines:
                return
            buf, ended, remain = self._tree_data
            if level < 0:
                raise IndexError
            was_ended = ended[level]
            ended[level] = False
            if level > 0:
                upbuffer = buf[level - 1]
                push_line = upbuffer.append
            else:
                f = self.file
                def push_line(line):
                    if f is not None:
                        print(line, file=f)
            it = iter(lines)
            if was_ended:
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

            if remain is not None:
                lines.clear()
            if level > 0 and remain[level - 1] is not None:
                # In unbuffered mode (with 'count' passed to tree_children)
                # we iterate up to the root and print everything immediately.
                level -= 1
                lines = upbuffer
                last = remain[level] <= 1
            else:
                return

    @contextmanager
    def tree_children(self, count=None):
        buf, ended, remain = self._tree_data
        level = len(buf)
        if remain and remain[level - 1] is None:
            # We are nested inside a tree_children() without count. Cannot
            # use unbufferd printing.
            count = None
        lines = []
        buf.append(lines)
        # When unbuffered, we start with ended state, so we get our tree
        # printed on the first nested line.
        ended.append(count is not None)
        remain.append(count)
        broken = False
        try:
            yield
        except BrokenPipeError:
            broken = True
            raise
        finally:
            ended[level] = True
            if not broken and count is None:
                self._tree_push_up(level, lines, True)
            buf.pop()
            ended.pop()
            remain.pop()

    def tree_next_child(self):
        buf, ended, remain = self._tree_data
        if buf:
            count = remain[-1]
            if count is not None:
                # We don't count down if nothing was printed.
                # For our tree to look correct, classes need to make sure
                # they print at least once for each child anyways.
                if not ended[-1]:
                    remain[-1] = count - 1
                    ended[-1] = True
            elif buf[-1]:
                ended[-1] = True

    def print_object(self, obj):
        obj.print(p=self)

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

    def print(self, p):
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


def print_objects(p, children):
    counters = p.counters
    with p.tree_children(len(children)):
        for obj in children:
            p.tree_next_child()
            if counters is not None:
                counters.num_objects += 1
            if 'numbers' in p.flags:
                p(f"Level object: {counters.num_objects}")
            yield obj.visit_print(p)


def format_bytes(data, fmt='02x'):
    if isinstance(data, (tuple, list)):
        return ', '.join(format_bytes(d) for d in data)
    else:
        return ' '.join(format(b, fmt) for b in data)


def format_bytes_multiline(data, width=16, fmt="02x", maxlines=128):
    if not data:
        return ["<empty>"]
    maxlen = maxlines * width
    lines = [' '.join(format(b, fmt)
                     for b in islice(data, row, row + width))
            for row in range(0, min(len(data), maxlen), width)]
    if len(data) > maxlen:
        lines.append(f"<{len(data) - maxlen} of {len(data)} bytes omitted>")
    return lines


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
    if not trans:
        return 'None'
    def format_floats(floats):
        return ', '.join(format(f, '.3f') for f in floats)
    return ', '.join(f"({format_floats(f)})" for f in trans)


# vim:set sw=4 ts=8 sts=4 et:
