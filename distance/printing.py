"""Utilities for printing object data."""


from contextlib import contextmanager
import traceback


class PrintContext(object):

    """Context class for printing objects."""

    def __init__(self, file, flags):
        self.file = file
        self.flags = flags
        # buffered lines, object finished
        self._tree_data = [], []

    @classmethod
    def for_test(clazz, file=None, flags=()):
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


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
