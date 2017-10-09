"""Handling of *args and **kw."""


DO_THROW = object()


class ArgTaker(object):

    def __init__(self, *args, **kw):
        self.args = args
        self.kwargs = kw
        self.maxarg = 0

    def __call__(self, index, kwname, default=DO_THROW):
        maxarg = self.maxarg
        if index is not None and index > maxarg:
            self.maxarg = index
        args = self.args
        if index is not None and index < len(args):
            return args[index]
        else:
            try:
                return self.kwargs.pop(kwname)
            except KeyError:
                if default == DO_THROW:
                    raise TypeError(f"missing argument: {kwname!r}")
                else:
                    return default

    def verify(self):
        if len(self.args) > self.maxarg + 1:
            raise TypeError(f"too many arguments (expected {self.maxarg})")
        if self.kwargs:
            raise TypeError(f"invalid kwargs: {self.kwargs}")


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
